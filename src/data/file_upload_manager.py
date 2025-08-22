"""
File Upload Manager for EchoPilot
Handles multiple file uploads with validation, processing status, and integration with knowledge base
"""

import logging
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import shutil
import gc
import psutil

from .document_processor import DocumentProcessor, IngestionPipeline
from .knowledge_base import KnowledgeBaseType, KnowledgeBaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of a file upload operation"""
    filename: str
    success: bool
    message: str
    chunks_created: int = 0
    file_size_mb: float = 0.0
    processing_time_seconds: float = 0.0


@dataclass
class UploadConfig:
    """Configuration for file uploads"""
    max_file_size_mb: float = 10.0
    max_files_per_batch: int = 10
    allowed_extensions: List[str] = None
    temp_directory: str = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.txt', '.md', '.json', '.csv', '.pdf', '.docx', '.doc', 
                                     '.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        if self.temp_directory is None:
            self.temp_directory = tempfile.gettempdir()


class FileUploadManager:
    """Manages file uploads with validation and processing"""
    
    def __init__(self, knowledge_base_manager: KnowledgeBaseManager, 
                 config: Optional[UploadConfig] = None):
        """
        Initialize file upload manager
        
        Args:
            knowledge_base_manager: KnowledgeBaseManager instance
            config: Optional upload configuration
        """
        self.kb_manager = knowledge_base_manager
        self.config = config or UploadConfig()
        self.document_processor = DocumentProcessor()
        self.ingestion_pipeline = IngestionPipeline(knowledge_base_manager, self.document_processor)
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.config.temp_directory, exist_ok=True)
        
        logger.info(f"FileUploadManager initialized with max_size={self.config.max_file_size_mb}MB, "
                   f"max_files={self.config.max_files_per_batch}")
    
    def validate_file(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate a single file before processing
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            file_path = Path(filename)
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.config.allowed_extensions:
                return False, f"File type {file_extension} not allowed. Supported types: {', '.join(self.config.allowed_extensions)}"
            
            # Check file size
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                return False, f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed ({self.config.max_file_size_mb}MB)"
            
            # Check if file is empty
            if len(file_content) == 0:
                return False, "File is empty"
            
            # Additional validation for specific file types
            if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # Validate image file header
                if not self._validate_image_header(file_content):
                    return False, "Invalid image file format"
            
            return True, "File validation successful"
            
        except Exception as e:
            logger.error(f"Error validating file {filename}: {e}")
            return False, f"Validation error: {e}"
    
    def validate_batch(self, files: List[Tuple[str, bytes]]) -> Tuple[bool, List[str]]:
        """
        Validate a batch of files
        
        Args:
            files: List of (filename, file_content) tuples
            
        Returns:
            Tuple of (all_valid, list_of_error_messages)
        """
        try:
            # Check batch size
            if len(files) > self.config.max_files_per_batch:
                return False, [f"Too many files ({len(files)}). Maximum allowed: {self.config.max_files_per_batch}"]
            
            errors = []
            all_valid = True
            
            # Validate each file
            for filename, file_content in files:
                is_valid, error_msg = self.validate_file(file_content, filename)
                if not is_valid:
                    all_valid = False
                    errors.append(f"{filename}: {error_msg}")
            
            return all_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating file batch: {e}")
            return False, [f"Batch validation error: {e}"]
    
    def upload_files(self, files: List[Tuple[str, bytes]], kb_type: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> List[UploadResult]:
        """
        Upload and process multiple files
        
        Args:
            files: List of (filename, file_content) tuples
            kb_type: Knowledge base type ('internal' or 'general')
            metadata: Optional metadata to attach to all files
            
        Returns:
            List of UploadResult objects
        """
        results = []
        start_time = datetime.now()
        
        try:
            # Validate batch first
            is_valid, errors = self.validate_batch(files)
            if not is_valid:
                # Return error results for all files
                for i, (filename, _) in enumerate(files):
                    error_msg = errors[i] if i < len(errors) else "Batch validation failed"
                    results.append(UploadResult(
                        filename=filename,
                        success=False,
                        message=error_msg
                    ))
                return results
            
            # Process each file
            for filename, file_content in files:
                result = self._process_single_file(
                    filename, file_content, kb_type, metadata
                )
                results.append(result)
            
            # Log batch summary
            successful = sum(1 for r in results if r.success)
            total_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Batch upload completed: {successful}/{len(files)} files successful in {total_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch upload: {e}")
            # Return error results for all files
            for filename, _ in files:
                results.append(UploadResult(
                    filename=filename,
                    success=False,
                    message=f"Batch processing error: {e}"
                ))
            return results
    
    def _process_single_file(self, filename: str, file_content: bytes, 
                           kb_type: str, metadata: Optional[Dict[str, Any]] = None) -> UploadResult:
        """
        Process a single file upload
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            kb_type: Knowledge base type
            metadata: Optional metadata
            
        Returns:
            UploadResult object
        """
        start_time = datetime.now()
        temp_file_path = None
        
        try:
            # Validate individual file
            is_valid, error_msg = self.validate_file(file_content, filename)
            if not is_valid:
                return UploadResult(
                    filename=filename,
                    success=False,
                    message=error_msg,
                    file_size_mb=len(file_content) / (1024 * 1024)
                )
            
            # Check memory limits before processing
            file_size_mb = len(file_content) / (1024 * 1024)
            can_process, memory_msg = self._check_memory_limits(file_size_mb)
            if not can_process:
                return UploadResult(
                    filename=filename,
                    success=False,
                    message=f"Memory limit exceeded: {memory_msg}",
                    file_size_mb=file_size_mb
                )
            
            # Create temporary file
            temp_file_path = self._create_temp_file(filename, file_content)
            
            # Add upload metadata
            upload_metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'original_filename': filename,
                'upload_source': 'streamlit_interface'
            }
            if metadata:
                upload_metadata.update(metadata)
            
            # Process file through ingestion pipeline (this already processes the file into chunks)
            success = self.ingestion_pipeline.ingest_file(
                file_path=temp_file_path,
                kb_type=kb_type,
                metadata=upload_metadata
            )
            
            if success:
                # Get processing stats without re-processing the file
                # Note: We need to estimate chunks created since ingestion_pipeline already processed it
                # This avoids the CPU/memory intensive double processing issue
                file_size_mb = len(file_content) / (1024 * 1024)
                estimated_chunks = max(1, int(file_size_mb * 1000 / self.document_processor.chunk_size))
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return UploadResult(
                    filename=filename,
                    success=True,
                    message=f"Successfully processed and ingested into knowledge base",
                    chunks_created=estimated_chunks,
                    file_size_mb=file_size_mb,
                    processing_time_seconds=processing_time
                )
            else:
                return UploadResult(
                    filename=filename,
                    success=False,
                    message="Failed to ingest into knowledge base",
                    file_size_mb=len(file_content) / (1024 * 1024)
                )
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return UploadResult(
                filename=filename,
                success=False,
                message=f"Processing error: {e}",
                file_size_mb=len(file_content) / (1024 * 1024)
            )
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
            
            # Force memory cleanup after processing
            self._cleanup_memory()
    
    def _create_temp_file(self, filename: str, file_content: bytes) -> str:
        """
        Create a temporary file with the uploaded content
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            
        Returns:
            Path to the temporary file
        """
        try:
            # Generate unique temp filename
            file_path = Path(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_filename = f"{timestamp}_{file_path.name}"
            temp_file_path = os.path.join(self.config.temp_directory, temp_filename)
            
            # Write content to temp file
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error creating temp file for {filename}: {e}")
            raise
    
    def _validate_image_header(self, file_content: bytes) -> bool:
        """
        Validate image file header to ensure it's a valid image
        
        Args:
            file_content: File content as bytes
            
        Returns:
            True if valid image header, False otherwise
        """
        try:
            # Check common image file signatures
            if len(file_content) < 4:
                return False
            
            # JPEG
            if file_content[:2] == b'\xff\xd8':
                return True
            
            # PNG
            if file_content[:8] == b'\x89PNG\r\n\x1a\n':
                return True
            
            # BMP
            if file_content[:2] == b'BM':
                return True
            
            # TIFF
            if file_content[:4] in [b'II*\x00', b'MM\x00*']:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating image header: {e}")
            return False
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """
        Get upload manager statistics and configuration
        
        Returns:
            Dictionary with upload manager stats
        """
        processor_stats = self.document_processor.get_processing_stats()
        
        return {
            'config': {
                'max_file_size_mb': self.config.max_file_size_mb,
                'max_files_per_batch': self.config.max_files_per_batch,
                'allowed_extensions': self.config.allowed_extensions,
                'temp_directory': self.config.temp_directory
            },
            'processor_stats': processor_stats,
            'upload_manager_version': '1.0.0'
        }
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up old temporary files
        
        Args:
            older_than_hours: Remove files older than this many hours
        """
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (older_than_hours * 3600)
            
            temp_dir = Path(self.config.temp_directory)
            if not temp_dir.exists():
                return
            
            removed_count = 0
            for file_path in temp_dir.glob('*'):
                if file_path.is_file():
                    try:
                        file_time = file_path.stat().st_mtime
                        if file_time < cutoff_time:
                            file_path.unlink()
                            removed_count += 1
                    except Exception as e:
                        logger.warning(f"Error removing old temp file {file_path}: {e}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old temporary files")
                
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'memory_mb': memory_info.rss / (1024 * 1024),
                'memory_percent': process.memory_percent(),
                'available_memory_mb': psutil.virtual_memory().available / (1024 * 1024)
            }
        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            return {'memory_mb': 0, 'memory_percent': 0, 'available_memory_mb': 0}
    
    def _cleanup_memory(self):
        """Force garbage collection and memory cleanup"""
        try:
            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Garbage collection freed {collected} objects")
        except Exception as e:
            logger.warning(f"Error during memory cleanup: {e}")
    
    def _check_memory_limits(self, file_size_mb: float) -> Tuple[bool, str]:
        """
        Check if there's enough memory to process the file
        
        Args:
            file_size_mb: Size of the file to process in MB
            
        Returns:
            Tuple of (can_process, message)
        """
        try:
            memory_stats = self._get_memory_usage()
            available_mb = memory_stats.get('available_memory_mb', 0)
            current_usage = memory_stats.get('memory_percent', 0)
            
            # Estimate memory needed (file size * 4 for processing overhead)
            estimated_memory_needed = file_size_mb * 4
            
            # Check if current usage is too high
            if current_usage > 85:
                return False, f"Current memory usage too high ({current_usage:.1f}%)"
            
            # Check if we have enough available memory
            if available_mb < estimated_memory_needed:
                return False, f"Insufficient memory (need {estimated_memory_needed:.1f}MB, available {available_mb:.1f}MB)"
            
            return True, "Memory check passed"
            
        except Exception as e:
            logger.warning(f"Memory check failed: {e}")
            return True, "Memory check failed, proceeding anyway"