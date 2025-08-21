"""
Knowledge Base management for EchoPilot
Handles ChromaDB cloud integration and role-based knowledge access
"""

import os
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBaseType(Enum):
    """Types of knowledge bases"""
    INTERNAL = "internal"  # Financial data, team structure, patents - Associates only
    GENERAL = "general"    # Services, FAQs, troubleshooting, T&Cs - Both roles


class SentenceTransformerEmbedding(EmbeddingFunction):
    """Custom embedding function using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        logger.info(f"Initialized embedding model: {model_name}")
    
    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for documents"""
        embeddings = self.model.encode(input).tolist()
        return embeddings


class KnowledgeBaseManager:
    """Manages ChromaDB cloud integration and knowledge base operations"""
    
    def __init__(self):
        """Initialize ChromaDB client and embedding function"""
        try:
            # Initialize embedding function
            self.embedding_function = SentenceTransformerEmbedding()
            
            # Initialize ChromaDB client
            self.client = self._init_chromadb_client()
            
            # Initialize collections
            self.internal_collection = None
            self.general_collection = None
            
            self._setup_collections()
            
            logger.info("KnowledgeBaseManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeBaseManager: {e}")
            raise
    
    def _init_chromadb_client(self) -> chromadb.Client:
        """Initialize ChromaDB client with cloud configuration"""
        try:
            # Try cloud configuration first
            chroma_api_key = os.getenv('CHROMADB_API_KEY')
            chroma_url = os.getenv('CHROMADB_URL', 'https://api.trychroma.com')
            
            if chroma_api_key:
                logger.info("Initializing ChromaDB cloud client")
                # For cloud setup (when available)
                client = chromadb.HttpClient(
                    host=chroma_url,
                    settings=chromadb.config.Settings(
                        chroma_api_impl="chromadb.api.fastapi.FastAPI",
                        chroma_server_auth_credentials=chroma_api_key
                    )
                )
            else:
                logger.warning("ChromaDB API key not found, using persistent local client")
                # Fallback to local persistent client
                client = chromadb.PersistentClient(path="./chroma_db")
            
            return client
            
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            logger.info("Falling back to in-memory client")
            # Ultimate fallback to in-memory client
            return chromadb.Client()
    
    def _setup_collections(self):
        """Set up knowledge base collections"""
        try:
            # Internal knowledge base (Associates only)
            self.internal_collection = self.client.get_or_create_collection(
                name="internal_knowledge_base",
                embedding_function=self.embedding_function,
                metadata={"description": "Internal knowledge base for associates only"}
            )
            
            # General knowledge base (Both roles)
            self.general_collection = self.client.get_or_create_collection(
                name="general_knowledge_base", 
                embedding_function=self.embedding_function,
                metadata={"description": "General knowledge base for all users"}
            )
            
            logger.info("Knowledge base collections initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup collections: {e}")
            raise
    
    def add_documents(self, 
                     documents: List[str], 
                     metadatas: List[Dict[str, Any]], 
                     kb_type: KnowledgeBaseType,
                     ids: Optional[List[str]] = None) -> bool:
        """
        Add documents to the specified knowledge base
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries for each document
            kb_type: Knowledge base type (INTERNAL or GENERAL)
            ids: Optional list of document IDs
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = self._get_collection(kb_type)
            
            if not ids:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to {kb_type.value} knowledge base")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to {kb_type.value}: {e}")
            return False
    
    def search_documents(self, 
                        query: str, 
                        kb_type: KnowledgeBaseType,
                        n_results: int = 5,
                        where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for relevant documents in the knowledge base
        
        Args:
            query: Search query text
            kb_type: Knowledge base type to search
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dict containing search results
        """
        try:
            collection = self._get_collection(kb_type)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            logger.info(f"Found {len(results['documents'][0])} results for query in {kb_type.value}")
            
            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0],
                'ids': results['ids'][0]
            }
            
        except Exception as e:
            logger.error(f"Search failed in {kb_type.value}: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
    
    def get_accessible_kb_types(self, user_role) -> List[KnowledgeBaseType]:
        """
        Get knowledge base types accessible to a user role
        
        Args:
            user_role: User role (associate/customer) - can be string or list
            
        Returns:
            List of accessible knowledge base types
        """
        # Handle both string and list inputs for user_role
        if isinstance(user_role, list):
            if len(user_role) > 0:
                normalized_role = str(user_role[0]).lower()
            else:
                logger.warning("Empty user_role list provided, defaulting to customer")
                normalized_role = 'customer'
        elif isinstance(user_role, str):
            normalized_role = user_role.lower()
        else:
            logger.warning(f"Invalid user_role type: {type(user_role)}, defaulting to customer")
            normalized_role = 'customer'
        
        if normalized_role == 'associate':
            return [KnowledgeBaseType.INTERNAL, KnowledgeBaseType.GENERAL]
        else:  # customer or any other role
            return [KnowledgeBaseType.GENERAL]
    
    def search_all_accessible(self, 
                            query: str, 
                            user_role: str,
                            n_results: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Search all knowledge bases accessible to the user role
        
        Args:
            query: Search query text
            user_role: User role (associate/customer)
            n_results: Number of results per knowledge base
            
        Returns:
            Dict with results from each accessible knowledge base
        """
        accessible_kbs = self.get_accessible_kb_types(user_role)
        all_results = {}
        
        for kb_type in accessible_kbs:
            results = self.search_documents(query, kb_type, n_results)
            if results['documents']:  # Only include if there are results
                all_results[kb_type.value] = results
        
        logger.info(f"Searched {len(accessible_kbs)} knowledge bases for role: {user_role}")
        return all_results
    
    def _get_collection(self, kb_type: KnowledgeBaseType):
        """Get the appropriate collection for knowledge base type"""
        if kb_type == KnowledgeBaseType.INTERNAL:
            return self.internal_collection
        else:
            return self.general_collection
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about knowledge base collections"""
        try:
            internal_count = self.internal_collection.count()
            general_count = self.general_collection.count()
            
            return {
                'internal_documents': internal_count,
                'general_documents': general_count,
                'total_documents': internal_count + general_count,
                'collections': ['internal_knowledge_base', 'general_knowledge_base']
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {'error': str(e)}
    
    def initialize_sample_data(self):
        """Initialize with sample knowledge base data for testing"""
        try:
            # Sample general knowledge base data
            general_docs = [
                "Our customer support is available 24/7 via chat, email, or phone. Response times are typically under 2 hours for priority issues.",
                "To reset your password, go to the login page and click 'Forgot Password'. Enter your email and follow the instructions sent to you.",
                "We offer three service tiers: Basic (free), Pro ($29/month), and Enterprise (custom pricing). Each tier includes different feature sets.",
                "Our refund policy allows full refunds within 30 days of purchase. No questions asked for the first 30 days.",
                "Technical issues can be reported through our support portal. Please include error messages and steps to reproduce the issue.",
                "Account upgrades take effect immediately. Downgrades take effect at the end of your current billing cycle.",
                "Data exports are available in CSV, JSON, and XML formats. Enterprise customers can schedule automated exports.",
                "Security features include 2FA, SSO integration, role-based permissions, and audit logging.",
                "API rate limits are 1000 requests per hour for free accounts, 10,000 for Pro, and unlimited for Enterprise.",
                "System maintenance is scheduled for the first Sunday of each month from 2-4 AM UTC."
            ]
            
            general_metadata = [
                {"category": "support", "type": "availability", "priority": "high"},
                {"category": "account", "type": "security", "priority": "high"},
                {"category": "billing", "type": "plans", "priority": "medium"},
                {"category": "billing", "type": "refunds", "priority": "high"},
                {"category": "support", "type": "technical", "priority": "high"},
                {"category": "billing", "type": "changes", "priority": "medium"},
                {"category": "data", "type": "export", "priority": "low"},
                {"category": "security", "type": "features", "priority": "high"},
                {"category": "api", "type": "limits", "priority": "medium"},
                {"category": "system", "type": "maintenance", "priority": "low"}
            ]
            
            # Sample internal knowledge base data (Associates only)
            internal_docs = [
                "Q4 revenue was $2.3M, representing 45% growth YoY. Enterprise segment grew 67% while SMB remained flat.",
                "Engineering team structure: 12 backend developers, 8 frontend, 4 DevOps, 3 QA engineers. Total team size is 27.",
                "Patent US10234567 covers our real-time data synchronization algorithm. Valid until 2041. No licensing deals currently.",
                "Customer churn rate is 3.2% monthly for Pro accounts, 1.1% for Enterprise. Top churn reasons: pricing and feature gaps.",
                "Sales pipeline shows $4.1M in qualified opportunities for Q1. 67% probability weighted value is $2.7M.",
                "Support ticket volume: 234 tickets last week, 23% increase. Average resolution time is 4.2 hours, target is 4 hours.",
                "Server costs are $23K/month on AWS. Database storage costs $8K/month. CDN costs $3K/month.",
                "Competitor analysis: Product X has 67% market share, we have 12%. Their pricing is 20% higher than ours.",
                "Employee headcount: 45 total, 15 engineering, 8 sales, 6 marketing, 5 support, 4 operations, 7 management.",
        "Feature usage stats: Dashboard (89% active users), Reports (45%), API (23%), Integrations (67%)."
            ]
            
            internal_metadata = [
                {"category": "financial", "type": "revenue", "confidentiality": "high"},
                {"category": "hr", "type": "team_structure", "confidentiality": "medium"},
                {"category": "legal", "type": "patents", "confidentiality": "high"},
                {"category": "metrics", "type": "churn", "confidentiality": "high"},
                {"category": "sales", "type": "pipeline", "confidentiality": "high"},
                {"category": "operations", "type": "support_metrics", "confidentiality": "medium"},
                {"category": "financial", "type": "costs", "confidentiality": "high"},
                {"category": "strategy", "type": "competitive", "confidentiality": "high"},
                {"category": "hr", "type": "headcount", "confidentiality": "medium"},
                {"category": "product", "type": "usage", "confidentiality": "medium"}
            ]
            
            # Add documents to knowledge bases
            self.add_documents(general_docs, general_metadata, KnowledgeBaseType.GENERAL)
            self.add_documents(internal_docs, internal_metadata, KnowledgeBaseType.INTERNAL)
            
            logger.info("Sample knowledge base data initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize sample data: {e}")
            return False