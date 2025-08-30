import os
from services import vector_store
import chromadb

def check_collections():
    """Check all collections and their data in ChromaDB"""
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="knowledgeBase")
    
    print("=== ChromaDB Collections ===")
    collections = client.list_collections()
    
    if not collections:
        print("No collections found!")
        return
    
    for collection in collections:
        print(f"\nCollection: {collection.name}")
        print(f"Document count: {collection.count()}")
        
        # Get first 5 documents to preview
        if collection.count() > 0:
            results = collection.peek(limit=5)
            print(f"Sample documents (first 5):")
            for i, doc in enumerate(results['documents']):
                print(f"  {i+1}. {doc[:100]}...")
                if results['metadatas'] and i < len(results['metadatas']):
                    print(f"     Metadata: {results['metadatas'][i]}")
            print("-" * 50)

def check_current_vector_store():
    """Check the vector store being used by services.py"""
    print("\n=== Current Vector Store Info ===")
    print(f"Collection name: {vector_store._collection.name}")
    print(f"Document count: {vector_store._collection.count()}")
    
    # Try a sample query
    print("\n=== Sample Query Test ===")
    try:
        results = vector_store.similarity_search("test", k=1)
        if results:
            print(f"Sample document: {results[0].page_content[:200]}...")
            print(f"Metadata: {results[0].metadata}")
        else:
            print("No documents found in current collection")
    except Exception as e:
        print(f"Error querying: {e}")

if __name__ == "__main__":
    check_collections()
    check_current_vector_store()