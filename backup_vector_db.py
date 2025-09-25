#!/usr/bin/env python3
"""
Vector Database Backup Script

This script creates a backup of the current ChromaDB vector store before
running metadata updates. It exports all documents, metadata, and embeddings
to a JSON file for recovery purposes.

Usage:
    python backup_vector_db.py [--output_file <filename>]

Example:
    python backup_vector_db.py --output_file backup_2025_01_15.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
import sqlite_fix  # Import before ChromaDB

from services import vector_store, db_collection_name
from logger_setup import setup_logger

logger = setup_logger()

def create_backup(output_file: str = None) -> bool:
    """Create a backup of the vector database"""

    # Generate default filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vector_db_backup_{timestamp}.json"

    logger.info("=" * 60)
    logger.info("VECTOR DATABASE BACKUP SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Collection: {db_collection_name}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)

    try:
        # Get all documents from the collection
        logger.info("Retrieving documents from ChromaDB...")
        collection = vector_store._collection

        results = collection.get(
            include=['metadatas', 'documents', 'embeddings']
        )

        if not results['ids']:
            logger.warning("No documents found in the vector store")
            return False

        document_count = len(results['ids'])
        logger.info(f"Found {document_count} documents to backup")

        # Prepare backup data
        backup_data = {
            'metadata': {
                'backup_timestamp': datetime.now().isoformat(),
                'collection_name': db_collection_name,
                'document_count': document_count,
                'script_version': '1.0'
            },
            'documents': []
        }

        # Process each document
        for i in range(document_count):
            # Handle embeddings - convert numpy array to list for JSON serialization
            embedding_data = None
            if results['embeddings'] is not None and len(results['embeddings']) > i:
                embedding = results['embeddings'][i]
                # Convert numpy array to list if needed
                if hasattr(embedding, 'tolist'):
                    embedding_data = embedding.tolist()
                else:
                    embedding_data = embedding

            doc_data = {
                'id': results['ids'][i],
                'document': results['documents'][i] if results['documents'] is not None and len(results['documents']) > i else None,
                'metadata': results['metadatas'][i] if results['metadatas'] is not None and len(results['metadatas']) > i else {},
                'embedding': embedding_data
            }
            backup_data['documents'].append(doc_data)

        # Write backup to file
        logger.info(f"Writing backup to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        # Verify backup file
        file_size = Path(output_file).stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        logger.info("=" * 60)
        logger.info("BACKUP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Backup completed successfully")
        logger.info(f"📄 Documents backed up: {document_count}")
        logger.info(f"💾 File size: {file_size_mb:.2f} MB")
        logger.info(f"📁 Backup file: {output_file}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        return False

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Create a backup of the ChromaDB vector store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--output_file',
        help='Output filename for the backup (default: auto-generated with timestamp)'
    )

    parser.add_argument(
        '--log_level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Set logging level
    import logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        success = create_backup(args.output_file)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Backup process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()