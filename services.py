
# Import SQLite3 fix BEFORE any ChromaDB imports
import sqlite_fix

from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
from langchain.schema.vectorstore import VectorStoreRetriever
from typing import List, Dict, Any, Optional
import os
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

embedding_model = SentenceTransformerEmbeddings('sentence-transformers/all-MiniLM-L6-v2')

persist_directory = 'knowledgeBase'
db_collection_name = "general_rentomojo"

# Create directory if it doesn't exist
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)

vector_store = Chroma(
    collection_name=db_collection_name,
    embedding_function=embedding_model,
    persist_directory=persist_directory
)

def create_tenant_aware_retriever(tenant_id: str, user_role: str, search_kwargs: Dict[str, Any] = None) -> VectorStoreRetriever:
    """
    Create a tenant-aware retriever with metadata filtering for multi-tenant RBAC

    Args:
        tenant_id (str): Unique identifier for the tenant
        user_role (str): User role for RBAC filtering (customer, vendor, associate, leadership, hr)
        search_kwargs (Dict[str, Any], optional): Additional search parameters

    Returns:
        VectorStoreRetriever: Configured retriever with tenant and role-based filtering
    """
    # Default search parameters
    default_search_kwargs = {
        "k": 4,  # Number of documents to retrieve
        "filter": {}
    }

    # Merge with provided search_kwargs
    if search_kwargs:
        default_search_kwargs.update(search_kwargs)

    # Build metadata filter for tenant and role-based access
    metadata_filter = build_metadata_filter(tenant_id, user_role)

    # Merge tenant filter with any existing filters
    if "filter" in default_search_kwargs:
        default_search_kwargs["filter"].update(metadata_filter)
    else:
        default_search_kwargs["filter"] = metadata_filter

    logger.info(f"Created tenant-aware retriever for tenant_id: {tenant_id}, user_role: {user_role}")
    logger.debug(f"Retriever filter: {default_search_kwargs['filter']}")

    # Create and return the retriever with tenant-aware filtering
    return vector_store.as_retriever(search_kwargs=default_search_kwargs)

def build_metadata_filter(tenant_id: str, user_role: str) -> Dict[str, Any]:
    """
    Build metadata filter for tenant isolation and role-based access control

    Args:
        tenant_id (str): Unique identifier for the tenant
        user_role (str): User role for RBAC filtering

    Returns:
        Dict[str, Any]: Metadata filter for ChromaDB
    """
    # Tenant isolation filter - documents must belong to the tenant
    metadata_filter = {
        "tenant_id": tenant_id
    }

    # Role-based access control filter
    # Documents are accessible if:
    # 1. User role is in the document's access_roles list, OR
    # 2. Document visibility is "Public"

    # ChromaDB supports $or operator for complex filtering
    # Documents accessible if user_role is in access_roles OR document_visibility is "Public"
    role_filter = {
        "$or": [
            {"access_roles": {"$contains": user_role}},
            {"document_visibility": "Public"}
        ]
    }

    # Combine tenant and role filters using $and operator
    combined_filter = {
        "$and": [
            metadata_filter,
            role_filter
        ]
    }

    logger.debug(f"Built metadata filter for tenant_id: {tenant_id}, user_role: {user_role}")
    return combined_filter

def get_vector_store_status(tenant_id: str = None) -> Dict[str, Any]:
    """
    Get vector store status with optional tenant filtering

    Args:
        tenant_id (str, optional): Filter status by tenant

    Returns:
        Dict[str, Any]: Vector store status information
    """
    try:
        # Get collection info
        collection = vector_store._collection

        if tenant_id:
            # Get tenant-specific document count
            # Note: ChromaDB doesn't have direct count with filter, so we use get() with filter
            tenant_filter = {"tenant_id": tenant_id}
            try:
                results = collection.get(
                    where=tenant_filter,
                    limit=1  # Just to check if any documents exist
                )
                # For actual count, we would need to get all and count (expensive for large collections)
                # This is a basic implementation - could be optimized with direct collection queries
                tenant_doc_count = len(results['ids']) if results['ids'] else 0
                has_tenant_docs = tenant_doc_count > 0
            except Exception as e:
                logger.warning(f"Error getting tenant-specific count: {e}")
                has_tenant_docs = False
                tenant_doc_count = 0
        else:
            has_tenant_docs = None
            tenant_doc_count = None

        # Get total collection count
        total_count = collection.count()

        status = {
            "status": "ready" if total_count > 0 else "empty",
            "document_count": total_count,
            "collection_name": db_collection_name,
            "tenant_document_count": tenant_doc_count,
            "has_tenant_documents": has_tenant_docs
        }

        logger.info(f"Vector store status retrieved for tenant: {tenant_id}")
        return status

    except Exception as e:
        logger.error(f"Error getting vector store status: {e}")
        return {
            "status": "error",
            "document_count": 0,
            "collection_name": db_collection_name,
            "error_message": str(e),
            "tenant_document_count": 0,
            "has_tenant_documents": False
        }
