"""
RAG (Retrieval Augmented Generation) engine for EchoPilot
Handles knowledge retrieval and response generation using Gemini
"""

from typing import List, Dict, Any
import logging
from .gemini_client import GeminiClient
from src.data.knowledge_base import KnowledgeBaseManager

# Configure logging
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval Augmented Generation engine for knowledge-based responses"""
    
    def __init__(self):
        """Initialize RAG engine with Gemini client and knowledge base"""
        # Initialize Gemini client for response generation
        self.gemini_client = GeminiClient()
        
        # Initialize knowledge base manager
        try:
            self.knowledge_base = KnowledgeBaseManager()
            logger.info("Knowledge base manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            self.knowledge_base = None
        
        logger.info("RAG Engine initialized")
    
    def retrieve_documents(self, query: str, user_role: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from knowledge bases based on user role
        
        Args:
            query: User query
            user_role: User role (associate/customer)
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.knowledge_base:
            logger.warning("Knowledge base not available, using fallback")
            return self._fallback_retrieve(query, user_role, top_k)
        
        try:
            # Search all accessible knowledge bases for the user role
            all_results = self.knowledge_base.search_all_accessible(
                query=query,
                user_role=user_role,
                n_results=top_k
            )
            
            # Convert to unified format
            documents = []
            for kb_name, results in all_results.items():
                for i, (doc, metadata, distance, doc_id) in enumerate(zip(
                    results['documents'],
                    results['metadatas'], 
                    results['distances'],
                    results['ids']
                )):
                    documents.append({
                        "content": doc,
                        "source": doc_id,
                        "score": 1 - distance,  # Convert distance to similarity score
                        "knowledge_base": kb_name,
                        "metadata": metadata
                    })
            
            # Sort by score and return top_k
            documents.sort(key=lambda x: x['score'], reverse=True)
            return documents[:top_k]
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return self._fallback_retrieve(query, user_role, top_k)
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]], chat_history: List[Dict[str, Any]], knowledge_bases: List[str]) -> str:
        """
        Generate response using retrieved context and chat history with Gemini
        
        Args:
            query: User query
            context_docs: Retrieved context documents
            chat_history: Previous conversation history
            knowledge_bases: List of knowledge bases used
            
        Returns:
            Generated response string
        """
        try:
            # Use Gemini client to generate RAG response
            response = self.gemini_client.generate_rag_response(
                user_query=query,
                context_documents=context_docs,
                knowledge_bases=knowledge_bases,
                chat_history=chat_history
            )
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback to simple response
            context_summary = self._summarize_context(context_docs)
            return f"Based on the available information from {', '.join(knowledge_bases)} knowledge base(s): {context_summary}. I hope this helps with your query about: {query}"
    
    def _summarize_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """Summarize context documents for response generation"""
        if not context_docs:
            return "No specific context found"
        
        # Simple concatenation for prototype
        return " ".join([doc.get("content", "")[:200] for doc in context_docs])
    
    def _fallback_retrieve(self, query: str, user_role: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Fallback document retrieval when knowledge base is unavailable"""
        mock_documents = []
        
        # Determine accessible knowledge bases based on role
        accessible_kbs = ['general']
        if user_role.lower() == 'associate':
            accessible_kbs.append('internal')
        
        # Generate knowledge base specific mock documents
        for kb in accessible_kbs:
            if kb == "general":
                mock_documents.extend([
                    {
                        "content": f"General information related to: {query}. Our platform provides comprehensive solutions for customer success management.",
                        "source": "general_kb_fallback",
                        "score": 0.85,
                        "knowledge_base": "general",
                        "metadata": {"category": "general", "type": "fallback"}
                    },
                    {
                        "content": "Frequently asked questions and troubleshooting guides are available in our documentation section.",
                        "source": "general_faq_fallback",
                        "score": 0.75,
                        "knowledge_base": "general",
                        "metadata": {"category": "support", "type": "fallback"}
                    }
                ])
            elif kb == "internal":
                mock_documents.extend([
                    {
                        "content": f"Internal documentation for: {query}. This includes detailed technical specifications and internal procedures.",
                        "source": "internal_docs_fallback",
                        "score": 0.90,
                        "knowledge_base": "internal",
                        "metadata": {"category": "internal", "type": "fallback", "confidentiality": "medium"}
                    },
                    {
                        "content": "Team structure and escalation procedures for handling complex customer issues.",
                        "source": "internal_procedures_fallback",
                        "score": 0.80,
                        "knowledge_base": "internal",
                        "metadata": {"category": "hr", "type": "fallback", "confidentiality": "medium"}
                    }
                ])
        
        # Sort by score and return top_k documents
        mock_documents.sort(key=lambda x: x['score'], reverse=True)
        return mock_documents[:top_k]
    
    def search_knowledge_base(self, query: str, user_role: str, chat_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search knowledge bases and generate response based on user role
        
        Args:
            query: User query
            user_role: User role (associate/customer)
            chat_history: Previous conversation history
            
        Returns:
            Response with generated text and metadata
        """
        try:
            # Retrieve relevant documents based on user role
            context_docs = self.retrieve_documents(query, user_role)
            
            # Get accessible knowledge bases for the user role
            if self.knowledge_base:
                accessible_kbs = [kb.value for kb in self.knowledge_base.get_accessible_kb_types(user_role)]
            else:
                accessible_kbs = ['general'] if user_role.lower() == 'customer' else ['general', 'internal']
            
            # Generate response using Gemini
            response_text = self.generate_response(
                query=query, 
                context_docs=context_docs, 
                chat_history=chat_history or [], 
                knowledge_bases=accessible_kbs
            )
            
            return {
                "response": response_text,
                "sources": context_docs,
                "knowledge_bases_used": accessible_kbs,
                "source_count": len(context_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in search_knowledge_base: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try your request again or contact support if the issue persists.",
                "sources": [],
                "knowledge_bases_used": [],
                "source_count": 0,
                "error": str(e)
            }
    
    def initialize_knowledge_base(self) -> bool:
        """
        Initialize knowledge base with sample data
        
        Returns:
            True if successful, False otherwise
        """
        if not self.knowledge_base:
            logger.error("Knowledge base manager not available")
            return False
        
        try:
            success = self.knowledge_base.initialize_sample_data()
            if success:
                logger.info("Knowledge base initialized with sample data")
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base
        
        Returns:
            Dictionary with knowledge base statistics
        """
        if not self.knowledge_base:
            return {"status": "unavailable", "error": "Knowledge base manager not initialized"}
        
        try:
            return self.knowledge_base.get_collection_stats()
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {"status": "error", "error": str(e)}