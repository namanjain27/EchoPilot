#!/usr/bin/env python3
"""
Vector Database Metadata Update Script for Multi-Tenant RBAC

This script updates existing documents in the ChromaDB vector store to include
the new multi-tenant metadata fields: tenant_id, access_roles, and document_visibility.

Usage:
    python update_existing_docs_metadata.py --tenant_id <tenant_id> --access_role <role> [--document_visibility <visibility>] [--dry_run]

Examples:
    # Dry run to see what would be updated
    python update_existing_docs_metadata.py --tenant_id "rentomojo_main" --access_role "customer" --dry_run

    # Update all docs for tenant "rentomojo_main" with customer access
    python update_existing_docs_metadata.py --tenant_id "rentomojo_main" --access_role "customer"

    # Update with private visibility
    python update_existing_docs_metadata.py --tenant_id "acme_corp" --access_role "vendor" --document_visibility "Private"
"""

import argparse
import sys
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite_fix  # Import before ChromaDB

# Import our existing services and models
from services import vector_store, db_collection_name
from api.models.requests import UserRole, DocumentVisibility
from logger_setup import setup_logger

# Initialize logger
logger = setup_logger()

class VectorDBMetadataUpdater:
    """Class to handle updating metadata for existing documents in ChromaDB"""

    def __init__(self):
        self.vector_store = vector_store
        self.collection = vector_store._collection
        self.updated_count = 0
        self.error_count = 0

    def validate_inputs(self, tenant_id: str, access_role: str, document_visibility: str) -> bool:
        """Validate input parameters"""
        try:
            # Validate access role
            UserRole(access_role)
            logger.info(f"✓ Valid access role: {access_role}")
        except ValueError:
            logger.error(f"✗ Invalid access role '{access_role}'. Must be one of: {[r.value for r in UserRole]}")
            return False

        try:
            # Validate document visibility
            DocumentVisibility(document_visibility)
            logger.info(f"✓ Valid document visibility: {document_visibility}")
        except ValueError:
            logger.error(f"✗ Invalid document visibility '{document_visibility}'. Must be one of: {[v.value for v in DocumentVisibility]}")
            return False

        # Validate tenant_id (basic check)
        if not tenant_id or len(tenant_id.strip()) == 0:
            logger.error("✗ tenant_id cannot be empty")
            return False

        logger.info(f"✓ Valid tenant_id: {tenant_id}")
        return True

    def get_existing_documents(self) -> Optional[Dict]:
        """Retrieve all existing documents from the vector store"""
        try:
            logger.info("Fetching existing documents from ChromaDB...")
            # Get all documents from the collection
            results = self.collection.get(
                include=['metadatas', 'documents']
            )

            if not results['ids']:
                logger.warning("No documents found in the vector store")
                return None

            logger.info(f"Found {len(results['ids'])} existing documents")
            return results

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return None

    def check_documents_need_update(self, documents: Dict) -> List[int]:
        """Check which documents need metadata updates"""
        docs_needing_update = []

        for i, metadata in enumerate(documents['metadatas']):
            needs_update = False
            missing_fields = []

            # Check for missing tenant metadata fields
            if 'tenant_id' not in metadata:
                needs_update = True
                missing_fields.append('tenant_id')

            if 'access_roles' not in metadata:
                needs_update = True
                missing_fields.append('access_roles')

            if 'document_visibility' not in metadata:
                needs_update = True
                missing_fields.append('document_visibility')

            if needs_update:
                docs_needing_update.append(i)
                logger.debug(f"Document {i} (ID: {documents['ids'][i]}) missing: {missing_fields}")

        logger.info(f"Documents needing update: {len(docs_needing_update)} out of {len(documents['ids'])}")
        return docs_needing_update

    def create_updated_metadata(self, original_metadata: Dict, tenant_id: str, access_role: str, document_visibility: str) -> Dict:
        """Create updated metadata by adding tenant fields to existing metadata"""
        updated_metadata = original_metadata.copy()

        # Add multi-tenant metadata fields
        updated_metadata.update({
            'tenant_id': tenant_id,
            'access_roles': access_role,  # Store as string since ChromaDB doesn't support lists
            'document_visibility': document_visibility,
            'metadata_updated_timestamp': datetime.now().isoformat(),
            'metadata_update_reason': 'multi_tenant_migration'
        })

        return updated_metadata

    def update_documents_metadata(self, documents: Dict, docs_to_update: List[int],
                                tenant_id: str, access_role: str, document_visibility: str,
                                dry_run: bool = False) -> bool:
        """Update metadata for specified documents"""
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No actual updates will be performed")

        try:
            updated_metadatas = []
            updated_ids = []

            for doc_index in docs_to_update:
                doc_id = documents['ids'][doc_index]
                original_metadata = documents['metadatas'][doc_index]

                # Create updated metadata
                updated_metadata = self.create_updated_metadata(
                    original_metadata, tenant_id, access_role, document_visibility
                )

                updated_metadatas.append(updated_metadata)
                updated_ids.append(doc_id)

                if dry_run:
                    logger.info(f"📄 Would update document {doc_id}:")
                    logger.info(f"   + tenant_id: {tenant_id}")
                    logger.info(f"   + access_roles: {access_role}")
                    logger.info(f"   + document_visibility: {document_visibility}")
                else:
                    logger.debug(f"Updating document {doc_id} metadata")

            if not dry_run:
                # Perform batch update
                logger.info(f"Updating metadata for {len(updated_ids)} documents...")
                self.collection.update(
                    ids=updated_ids,
                    metadatas=updated_metadatas
                )

                self.updated_count = len(updated_ids)
                logger.info(f"✅ Successfully updated {self.updated_count} documents")
            else:
                logger.info(f"🔍 DRY RUN: Would update {len(updated_ids)} documents")

            return True

        except Exception as e:
            logger.error(f"Error updating documents: {str(e)}")
            self.error_count += 1
            return False

    def verify_updates(self, updated_ids: List[str], tenant_id: str, access_role: str) -> bool:
        """Verify that the updates were applied correctly"""
        try:
            logger.info("Verifying updates...")

            # Sample a few documents to verify
            sample_size = min(3, len(updated_ids))
            sample_ids = updated_ids[:sample_size]

            results = self.collection.get(
                ids=sample_ids,
                include=['metadatas']
            )

            verification_passed = True
            for i, metadata in enumerate(results['metadatas']):
                doc_id = sample_ids[i]

                if metadata.get('tenant_id') != tenant_id:
                    logger.error(f"❌ Verification failed for {doc_id}: tenant_id mismatch")
                    verification_passed = False

                if metadata.get('access_roles') != access_role:
                    logger.error(f"❌ Verification failed for {doc_id}: access_role mismatch")
                    verification_passed = False

                if verification_passed:
                    logger.debug(f"✅ Verification passed for {doc_id}")

            if verification_passed:
                logger.info("✅ Update verification successful")
            else:
                logger.error("❌ Update verification failed")

            return verification_passed

        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            return False

    def run_update(self, tenant_id: str, access_role: str, document_visibility: str = "Public", dry_run: bool = False):
        """Main method to run the metadata update process"""
        logger.info("=" * 60)
        logger.info("VECTOR DATABASE METADATA UPDATE SCRIPT")
        logger.info("=" * 60)
        logger.info(f"Target Collection: {db_collection_name}")
        logger.info(f"Tenant ID: {tenant_id}")
        logger.info(f"Access Role: {access_role}")
        logger.info(f"Document Visibility: {document_visibility}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info("=" * 60)

        # Step 1: Validate inputs
        if not self.validate_inputs(tenant_id, access_role, document_visibility):
            logger.error("❌ Input validation failed")
            return False

        # Step 2: Get existing documents
        documents = self.get_existing_documents()
        if not documents:
            logger.error("❌ No documents found or error retrieving documents")
            return False

        # Step 3: Check which documents need updates
        docs_to_update = self.check_documents_need_update(documents)
        if not docs_to_update:
            logger.info("✅ All documents already have the required metadata fields")
            return True

        # Step 4: Update documents
        success = self.update_documents_metadata(
            documents, docs_to_update, tenant_id, access_role, document_visibility, dry_run
        )

        if not success:
            logger.error("❌ Update process failed")
            return False

        # Step 5: Verify updates (only if not dry run)
        if not dry_run:
            updated_ids = [documents['ids'][i] for i in docs_to_update]
            if not self.verify_updates(updated_ids, tenant_id, access_role):
                logger.error("❌ Update verification failed")
                return False

        # Summary
        logger.info("=" * 60)
        logger.info("UPDATE SUMMARY")
        logger.info("=" * 60)
        if dry_run:
            logger.info(f"📊 Documents that would be updated: {len(docs_to_update)}")
            logger.info("🔍 This was a dry run - no actual changes made")
        else:
            logger.info(f"📊 Documents updated: {self.updated_count}")
            logger.info(f"❌ Errors encountered: {self.error_count}")
            logger.info("✅ Update process completed successfully")
        logger.info("=" * 60)

        return True

def main():
    """Main function to handle command line arguments and run the update"""
    parser = argparse.ArgumentParser(
        description="Update existing vector database documents with multi-tenant metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--tenant_id',
        required=True,
        help='Tenant ID to assign to all existing documents'
    )

    parser.add_argument(
        '--access_role',
        required=True,
        choices=[role.value for role in UserRole],
        help=f'Access role to assign to all existing documents. Choices: {[role.value for role in UserRole]}'
    )

    parser.add_argument(
        '--document_visibility',
        default='Public',
        choices=[vis.value for vis in DocumentVisibility],
        help=f'Document visibility level. Default: Public. Choices: {[vis.value for vis in DocumentVisibility]}'
    )

    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='Perform a dry run without making actual changes'
    )

    parser.add_argument(
        '--log_level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        # Create updater and run update
        updater = VectorDBMetadataUpdater()
        success = updater.run_update(
            tenant_id=args.tenant_id,
            access_role=args.access_role,
            document_visibility=args.document_visibility,
            dry_run=args.dry_run
        )

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Update process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()