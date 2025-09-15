from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import tempfile
import os
from pathlib import Path

from ..models.responses import KBUploadResponse
from data_ingestion import ingest_file_with_feedback

router = APIRouter(prefix="/api/v1", tags=["knowledge_base"])

@router.post("/knowledge-base/upload", response_model=KBUploadResponse)
async def upload_files_to_kb(
    files: List[UploadFile] = File(...)
):
    """
    Upload files to knowledge base for ingestion
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file count (max 5 files)
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed per request")
    
    results = []
    total_chunks = 0
    errors = []
    successful_files = 0
    
    # Supported file types
    supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
    
    for file in files:
        try:
            # Validate file size (10MB limit)
            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:  # 10MB
                error_msg = f"File {file.filename} exceeds 10MB size limit"
                errors.append(error_msg)
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "message": error_msg,
                    "chunks_created": 0
                })
                continue
            
            # Validate file type
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in supported_extensions:
                error_msg = f"File {file.filename} has unsupported format: {file_extension}"
                errors.append(error_msg)
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "message": error_msg,
                    "chunks_created": 0
                })
                continue
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Process file using existing ingestion function
                result = ingest_file_with_feedback(tmp_file_path, file.filename)
                
                if result["success"]:
                    successful_files += 1
                    # Extract chunk count from success message
                    chunks_created = 0
                    if "chunks" in result["message"]:
                        try:
                            # Extract number from message like "Successfully processed 15 chunks"
                            chunks_created = int(result["message"].split()[2])
                            total_chunks += chunks_created
                        except (IndexError, ValueError):
                            chunks_created = 0
                    
                    results.append({
                        "file_name": file.filename,
                        "success": True,
                        "message": result["message"],
                        "chunks_created": chunks_created
                    })
                else:
                    errors.append(f"{file.filename}: {result['message']}")
                    results.append({
                        "file_name": file.filename,
                        "success": False,
                        "message": result["message"],
                        "chunks_created": 0
                    })
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    
        except Exception as e:
            error_msg = f"Error processing {file.filename}: {str(e)}"
            errors.append(error_msg)
            results.append({
                "file_name": file.filename,
                "success": False,
                "message": error_msg,
                "chunks_created": 0
            })
    
    # Determine overall success
    overall_success = successful_files > 0 and len(errors) == 0
    
    return KBUploadResponse(
        success=overall_success,
        files_processed=successful_files,
        chunks_created=total_chunks,
        errors=errors,
        details=results
    )