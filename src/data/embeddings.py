"""
Embedding utilities for EchoPilot
Handles document embedding generation and similarity computations
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages document embeddings and similarity operations"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding manager with specified model
        
        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Sentence transformer model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            logger.warning("Embedding operations will not be available")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if embedding model is available"""
        return self.model is not None
    
    def encode_documents(self, documents: List[str]) -> Optional[np.ndarray]:
        """
        Generate embeddings for a list of documents
        
        Args:
            documents: List of document texts
            
        Returns:
            Numpy array of embeddings or None if model unavailable
        """
        if not self.is_available():
            logger.error("Embedding model not available")
            return None
        
        try:
            embeddings = self.model.encode(documents, convert_to_numpy=True)
            logger.info(f"Generated embeddings for {len(documents)} documents")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return None
    
    def encode_single(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            Numpy array embedding or None if model unavailable
        """
        if not self.is_available():
            logger.error("Embedding model not available")
            return None
        
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return None
    
    def compute_similarities(self, 
                           query_embedding: np.ndarray, 
                           document_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarities between query and document embeddings
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Array of document embedding vectors
            
        Returns:
            Array of similarity scores
        """
        try:
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norms = document_embeddings / np.linalg.norm(document_embeddings, axis=1, keepdims=True)
            
            # Compute cosine similarities
            similarities = np.dot(doc_norms, query_norm)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to compute similarities: {e}")
            return np.array([])
    
    def find_most_similar(self, 
                         query: str, 
                         documents: List[str], 
                         top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar documents to a query
        
        Args:
            query: Query text
            documents: List of document texts
            top_k: Number of top results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.is_available():
            logger.error("Embedding model not available")
            return []
        
        try:
            # Generate embeddings
            query_embedding = self.encode_single(query)
            if query_embedding is None:
                return []
            
            document_embeddings = self.encode_documents(documents)
            if document_embeddings is None:
                return []
            
            # Compute similarities
            similarities = self.compute_similarities(query_embedding, document_embeddings)
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append((documents[idx], float(similarities[idx])))
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to find similar documents: {e}")
            return []
    
    def batch_similarity_search(self, 
                               queries: List[str], 
                               document_corpus: List[str],
                               top_k: int = 5) -> Dict[str, List[Tuple[str, float]]]:
        """
        Perform similarity search for multiple queries
        
        Args:
            queries: List of query texts
            document_corpus: List of all document texts
            top_k: Number of top results per query
            
        Returns:
            Dict mapping queries to their top similar documents
        """
        if not self.is_available():
            logger.error("Embedding model not available")
            return {}
        
        results = {}
        
        try:
            # Pre-compute document embeddings once
            logger.info("Pre-computing document embeddings for batch search")
            document_embeddings = self.encode_documents(document_corpus)
            if document_embeddings is None:
                return {}
            
            # Process each query
            for query in queries:
                query_embedding = self.encode_single(query)
                if query_embedding is None:
                    results[query] = []
                    continue
                
                similarities = self.compute_similarities(query_embedding, document_embeddings)
                top_indices = np.argsort(similarities)[::-1][:top_k]
                
                query_results = []
                for idx in top_indices:
                    query_results.append((document_corpus[idx], float(similarities[idx])))
                
                results[query] = query_results
            
            logger.info(f"Completed batch similarity search for {len(queries)} queries")
            return results
            
        except Exception as e:
            logger.error(f"Failed in batch similarity search: {e}")
            return {}
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str) -> bool:
        """
        Save embeddings to file
        
        Args:
            embeddings: Numpy array of embeddings
            filepath: Path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            np.save(filepath, embeddings)
            logger.info(f"Saved embeddings to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")
            return False
    
    def load_embeddings(self, filepath: str) -> Optional[np.ndarray]:
        """
        Load embeddings from file
        
        Args:
            filepath: Path to embeddings file
            
        Returns:
            Loaded embeddings array or None if failed
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Embeddings file not found: {filepath}")
                return None
            
            embeddings = np.load(filepath)
            logger.info(f"Loaded embeddings from {filepath}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        if not self.is_available():
            return {"status": "unavailable", "model": self.model_name}
        
        try:
            # Get model dimensions
            sample_embedding = self.encode_single("test")
            dimensions = sample_embedding.shape[0] if sample_embedding is not None else 0
            
            return {
                "status": "available",
                "model": self.model_name,
                "dimensions": dimensions,
                "max_sequence_length": getattr(self.model, 'max_seq_length', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"status": "error", "model": self.model_name, "error": str(e)}


# Global embedding manager instance
_embedding_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get global embedding manager instance"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager