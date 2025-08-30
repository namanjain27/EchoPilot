import chromadb
import shutil
import os
from pathlib import Path

def cleanup_collections():
    """
    Delete all ChromaDB collections except 'general_rentomojo'
    """
    persist_directory = 'knowledgeBase'
    keep_collection = 'general_rentomojo'
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=persist_directory)
        
        print("=== ChromaDB Collection Cleanup ===")
        print(f"Keeping collection: '{keep_collection}'")
        print(f"Directory: {persist_directory}")
        
        # List all collections
        collections = client.list_collections()
        
        if not collections:
            print("No collections found!")
            return
        
        print(f"\nFound {len(collections)} collection(s):")
        for collection in collections:
            print(f"  - {collection.name} (Documents: {collection.count()})")
        
        # Delete collections that are not the one we want to keep
        deleted_collections = []
        for collection in collections:
            if collection.name != keep_collection:
                print(f"\nDeleting collection: '{collection.name}'...")
                client.delete_collection(collection.name)
                deleted_collections.append(collection.name)
            else:
                print(f"\nKeeping collection: '{collection.name}' (Documents: {collection.count()})")
        
        if deleted_collections:
            print(f"\n✅ Successfully deleted {len(deleted_collections)} collection(s):")
            for name in deleted_collections:
                print(f"  - {name}")
        else:
            print(f"\n✅ No collections to delete. Only '{keep_collection}' exists.")
            
        # Clean up orphaned directories in knowledgeBase
        print("\n=== Cleaning up orphaned directories ===")
        cleanup_orphaned_dirs(persist_directory, keep_collection)
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return False
    
    return True

def cleanup_orphaned_dirs(persist_directory, keep_collection):
    """
    Remove any orphaned collection directories that might be left behind
    """
    if not os.path.exists(persist_directory):
        print("Knowledge base directory doesn't exist")
        return
    
    # Get current collections after cleanup
    try:
        client = chromadb.PersistentClient(path=persist_directory)
        remaining_collections = [col.name for col in client.list_collections()]
        
        # Look for directories that might be collection folders
        for item in os.listdir(persist_directory):
            item_path = os.path.join(persist_directory, item)
            
            # Skip files and known directories
            if not os.path.isdir(item_path):
                continue
            if item in ['__pycache__', '.git']:
                continue
            if item.endswith('.pdf') or item.endswith('.docx') or item.endswith('.txt'):
                continue
                
            # Check if it's a UUID-like directory (collection folder)
            if len(item) == 36 and item.count('-') == 4:  # UUID format
                print(f"Found orphaned collection directory: {item}")
                try:
                    shutil.rmtree(item_path)
                    print(f"  ✅ Removed orphaned directory: {item}")
                except Exception as e:
                    print(f"  ❌ Failed to remove directory {item}: {e}")
            elif item not in remaining_collections and item != 'chroma.sqlite3':
                # Check if it looks like a collection name directory
                print(f"Found potential orphaned directory: {item}")
                response = input(f"Delete directory '{item}'? (y/N): ").lower()
                if response == 'y':
                    try:
                        shutil.rmtree(item_path)
                        print(f"  ✅ Removed directory: {item}")
                    except Exception as e:
                        print(f"  ❌ Failed to remove directory {item}: {e}")
    
    except Exception as e:
        print(f"Error during orphaned directory cleanup: {e}")

def verify_remaining_collection():
    """
    Verify that the kept collection is working properly
    """
    try:
        from services import vector_store
        print(f"\n=== Verifying '{vector_store._collection.name}' collection ===")
        count = vector_store._collection.count()
        print(f"Document count: {count}")
        
        if count > 0:
            # Try a test query
            results = vector_store.similarity_search("test", k=1)
            if results:
                print("✅ Collection is accessible and contains data")
                print(f"Sample document preview: {results[0].page_content[:100]}...")
            else:
                print("⚠️  Collection exists but query returned no results")
        else:
            print("⚠️  Collection is empty - you may need to re-ingest data")
            
    except ImportError:
        print("Cannot verify collection - services module not available")
    except Exception as e:
        print(f"Error verifying collection: {e}")

if __name__ == "__main__":
    print("This will delete ALL ChromaDB collections except 'general_rentomojo'")
    print("Make sure this is what you want to do!")
    
    response = input("\nProceed with cleanup? (y/N): ").lower()
    if response == 'y':
        if cleanup_collections():
            verify_remaining_collection()
        print("\nCleanup completed!")
    else:
        print("Cleanup cancelled.")