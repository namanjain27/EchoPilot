#!/usr/bin/env python3
"""
Vector Database Metadata Inspection Script

This script inspects the current metadata structure of documents in the ChromaDB
vector store to understand what fields exist and identify which documents need
multi-tenant metadata updates.

Usage:
    python inspect_vector_db_metadata.py [--sample_size <number>] [--show_examples]

Examples:
    # Quick overview
    python inspect_vector_db_metadata.py

    # Show 10 example documents
    python inspect_vector_db_metadata.py --sample_size 10 --show_examples

    # Full analysis
    python inspect_vector_db_metadata.py --sample_size 0 --show_examples
"""

import argparse
import sys
from collections import Counter, defaultdict
from datetime import datetime
import sqlite_fix  # Import before ChromaDB

from services import vector_store, db_collection_name
from logger_setup import setup_logger

logger = setup_logger()

class VectorDBInspector:
    """Class to inspect vector database metadata"""

    def __init__(self):
        self.vector_store = vector_store
        self.collection = vector_store._collection

    def get_documents_sample(self, sample_size: int = 5) -> dict:
        """Get a sample of documents for analysis"""
        try:
            logger.info("Retrieving documents from ChromaDB...")

            results = self.collection.get(
                include=['metadatas', 'documents'],
                limit=sample_size if sample_size > 0 else None
            )

            if not results['ids']:
                logger.warning("No documents found in the vector store")
                return None

            logger.info(f"Retrieved {len(results['ids'])} documents for analysis")
            return results

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return None

    def analyze_metadata_fields(self, documents: dict) -> dict:
        """Analyze what metadata fields exist across all documents"""
        field_counter = Counter()
        field_examples = defaultdict(set)
        tenant_fields_count = 0
        documents_with_tenant_fields = []

        for i, metadata in enumerate(documents['metadatas']):
            doc_id = documents['ids'][i]

            # Count all fields
            for field in metadata.keys():
                field_counter[field] += 1
                # Store a few example values (limit to avoid memory issues)
                if len(field_examples[field]) < 3:
                    field_examples[field].add(str(metadata[field])[:50])

            # Check for tenant-specific fields
            has_tenant_fields = all(field in metadata for field in ['tenant_id', 'access_roles', 'document_visibility'])
            if has_tenant_fields:
                tenant_fields_count += 1
                documents_with_tenant_fields.append(doc_id)

        return {
            'field_counter': field_counter,
            'field_examples': field_examples,
            'tenant_fields_count': tenant_fields_count,
            'documents_with_tenant_fields': documents_with_tenant_fields,
            'total_documents': len(documents['ids'])
        }

    def print_analysis_report(self, analysis: dict, show_examples: bool = False):
        """Print a formatted analysis report"""
        logger.info("=" * 70)
        logger.info("VECTOR DATABASE METADATA ANALYSIS REPORT")
        logger.info("=" * 70)
        logger.info(f"Collection: {db_collection_name}")
        logger.info(f"Total Documents Analyzed: {analysis['total_documents']}")
        logger.info(f"Analysis Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 70)

        # Multi-tenant field status
        logger.info("MULTI-TENANT METADATA STATUS")
        logger.info("-" * 35)
        logger.info(f"Documents with tenant fields: {analysis['tenant_fields_count']}")
        logger.info(f"Documents needing update: {analysis['total_documents'] - analysis['tenant_fields_count']}")

        if analysis['tenant_fields_count'] > 0:
            logger.info("✅ Some documents already have multi-tenant metadata")
            if show_examples and analysis['documents_with_tenant_fields']:
                logger.info(f"Examples: {analysis['documents_with_tenant_fields'][:3]}")
        else:
            logger.info("⚠️  No documents have multi-tenant metadata yet")

        # Field analysis
        logger.info("\nMETADATA FIELDS ANALYSIS")
        logger.info("-" * 25)
        logger.info(f"Total unique fields found: {len(analysis['field_counter'])}")

        # Check for specific fields we expect
        tenant_fields = ['tenant_id', 'access_roles', 'document_visibility']
        logger.info("\nRequired Multi-tenant Fields:")
        for field in tenant_fields:
            count = analysis['field_counter'].get(field, 0)
            status = "✅" if count > 0 else "❌"
            logger.info(f"  {status} {field}: {count}/{analysis['total_documents']} documents")

        # Common fields
        logger.info("\nMost Common Metadata Fields:")
        for field, count in analysis['field_counter'].most_common(10):
            percentage = (count / analysis['total_documents']) * 100
            logger.info(f"  📊 {field}: {count}/{analysis['total_documents']} ({percentage:.1f}%)")

        if show_examples:
            logger.info("\nFIELD EXAMPLES")
            logger.info("-" * 15)
            for field, examples in list(analysis['field_examples'].items())[:10]:
                logger.info(f"  {field}: {list(examples)}")

        logger.info("=" * 70)

    def show_sample_documents(self, documents: dict, num_samples: int = 3):
        """Show a few sample documents with their metadata"""
        logger.info("SAMPLE DOCUMENTS")
        logger.info("-" * 17)

        num_to_show = min(num_samples, len(documents['ids']))

        for i in range(num_to_show):
            doc_id = documents['ids'][i]
            metadata = documents['metadatas'][i]
            content_preview = documents['documents'][i][:100] + "..." if documents['documents'][i] else "No content"

            logger.info(f"\nDocument {i+1}: {doc_id}")
            logger.info(f"Content Preview: {content_preview}")
            logger.info("Metadata:")
            for key, value in metadata.items():
                logger.info(f"  {key}: {value}")

        logger.info("=" * 70)

    def run_inspection(self, sample_size: int = 5, show_examples: bool = False, show_sample_docs: bool = False):
        """Run the complete inspection process"""
        # Get document sample
        documents = self.get_documents_sample(sample_size)
        if not documents:
            return False

        # Analyze metadata
        analysis = self.analyze_metadata_fields(documents)

        # Print reports
        self.print_analysis_report(analysis, show_examples)

        if show_sample_docs:
            self.show_sample_documents(documents, 3)

        # Recommendations
        logger.info("RECOMMENDATIONS")
        logger.info("-" * 15)
        if analysis['tenant_fields_count'] == 0:
            logger.info("🔧 All documents need multi-tenant metadata updates")
            logger.info("   Run: python update_existing_docs_metadata.py --tenant_id <your_tenant> --access_role <role> --dry_run")
        elif analysis['tenant_fields_count'] < analysis['total_documents']:
            logger.info(f"🔧 {analysis['total_documents'] - analysis['tenant_fields_count']} documents need updates")
            logger.info("   Run: python update_existing_docs_metadata.py --tenant_id <your_tenant> --access_role <role> --dry_run")
        else:
            logger.info("✅ All documents have multi-tenant metadata")

        logger.info("\n💾 Consider creating a backup before updates:")
        logger.info("   python backup_vector_db.py")
        logger.info("=" * 70)

        return True

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Inspect ChromaDB vector store metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--sample_size',
        type=int,
        default=5,
        help='Number of documents to analyze (0 = all documents, default: 5)'
    )

    parser.add_argument(
        '--show_examples',
        action='store_true',
        help='Show example values for metadata fields'
    )

    parser.add_argument(
        '--show_sample_docs',
        action='store_true',
        help='Show sample documents with full metadata'
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
        inspector = VectorDBInspector()
        success = inspector.run_inspection(
            sample_size=args.sample_size,
            show_examples=args.show_examples,
            show_sample_docs=args.show_sample_docs
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Inspection interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()