#!/usr/bin/env python3
"""
Test script for RAG scoring service
Demonstrates how to use the scoring algorithms
"""

import sys
from datetime import datetime, timedelta
from langchain.schema import Document
from rag_scoring import RAGScoringService, score_documents

def create_test_documents():
    """Create sample documents with different metadata for testing"""

    # Document 1: High quality, recent, structured
    doc1_metadata = {
        "source": "/test/important_guide.pdf",
        "filename": "important_guide.pdf",
        "file_extension": ".pdf",
        "file_size_bytes": 50000,
        "ingestion_timestamp": datetime.now().isoformat(),
        "file_modified_timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
        "file_created_timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
        "chunk_index": 0,
        "total_chunks": 5,
        "chunk_position_ratio": 0.0,
        "word_count": 250,
        "char_count": 1500,
        "content_density": 0.167,
        "document_type": "formatted_document",
        "is_first_chunk": True,
        "is_last_chunk": False,
        "page_number": 1,
        "is_first_page": True
    }

    doc1 = Document(
        page_content="This comprehensive guide covers machine learning fundamentals including supervised learning, unsupervised learning, and neural networks. It provides practical examples and implementation details for building effective AI systems.",
        metadata=doc1_metadata
    )

    # Document 2: Medium quality, older
    doc2_metadata = {
        "source": "/test/old_notes.txt",
        "filename": "old_notes.txt",
        "file_extension": ".txt",
        "file_size_bytes": 15000,
        "ingestion_timestamp": (datetime.now() - timedelta(hours=12)).isoformat(),
        "file_modified_timestamp": (datetime.now() - timedelta(days=180)).isoformat(),
        "file_created_timestamp": (datetime.now() - timedelta(days=200)).isoformat(),
        "chunk_index": 2,
        "total_chunks": 4,
        "chunk_position_ratio": 0.5,
        "word_count": 120,
        "char_count": 800,
        "content_density": 0.15,
        "document_type": "plain_text",
        "is_first_chunk": False,
        "is_last_chunk": False
    }

    doc2 = Document(
        page_content="Machine learning algorithms can be categorized into different types. Some basic information about classification and regression techniques.",
        metadata=doc2_metadata
    )

    # Document 3: Lower quality, very recent but sparse content
    doc3_metadata = {
        "source": "/test/quick_note.md",
        "filename": "quick_note.md",
        "file_extension": ".md",
        "file_size_bytes": 2000,
        "ingestion_timestamp": datetime.now().isoformat(),
        "file_modified_timestamp": datetime.now().isoformat(),
        "file_created_timestamp": datetime.now().isoformat(),
        "chunk_index": 0,
        "total_chunks": 1,
        "chunk_position_ratio": 0.0,
        "word_count": 30,
        "char_count": 200,
        "content_density": 0.15,
        "document_type": "structured_text",
        "is_first_chunk": True,
        "is_last_chunk": True
    }

    doc3 = Document(
        page_content="AI and machine learning notes",
        metadata=doc3_metadata
    )

    return [doc1, doc2, doc3]

def test_scoring_service():
    """Test the RAG scoring service with sample data"""

    print("=== RAG Scoring Service Test ===\n")

    # Create test data
    query = "machine learning fundamentals and neural networks"
    documents = create_test_documents()
    # Simulate vector search similarity scores
    similarity_scores = [0.85, 0.65, 0.45]  # doc1 most similar, doc3 least

    print(f"Query: '{query}'")
    print(f"Testing with {len(documents)} documents\n")

    # Initialize scoring service
    scorer = RAGScoringService()

    print("Scoring Configuration:")
    print(f"- Semantic weight: {scorer.semantic_weight}")
    print(f"- Keyword weight: {scorer.keyword_weight}")
    print(f"- Quality weight: {scorer.quality_weight}")
    print(f"- Recency weight: {scorer.recency_weight}\n")

    # Test individual scoring components
    print("=== Individual Score Components ===")

    semantic_scores = scorer.compute_semantic_scores(documents, similarity_scores)
    print(f"Semantic scores: {[f'{s:.3f}' for s in semantic_scores]}")

    keyword_scores = scorer.compute_keyword_scores(query, documents)
    print(f"Keyword scores: {[f'{s:.3f}' for s in keyword_scores]}")

    quality_scores = scorer.compute_quality_scores(documents)
    print(f"Quality scores: {[f'{s:.3f}' for s in quality_scores]}")

    recency_scores = scorer.compute_recency_scores(documents)
    print(f"Recency scores: {[f'{s:.3f}' for s in recency_scores]}\n")

    # Test combined scoring
    print("=== Combined Scoring Results ===")
    scored_docs = scorer.compute_combined_scores(query, documents, similarity_scores)

    for i, (doc, score) in enumerate(scored_docs):
        filename = doc.metadata.get('filename', 'unknown')
        doc_type = doc.metadata.get('document_type', 'unknown')
        word_count = doc.metadata.get('word_count', 0)
        print(f"Rank {i+1}: {filename}")
        print(f"  - Combined Score: {score:.3f}")
        print(f"  - Document Type: {doc_type}")
        print(f"  - Word Count: {word_count}")
        print(f"  - Content Preview: {doc.page_content[:60]}...")
        print()

    # Test threshold filtering
    print("=== Threshold Filtering (0.4) ===")
    filtered_docs = scorer.filter_by_threshold(scored_docs, threshold=0.4)
    print(f"Documents above threshold: {len(filtered_docs)}/{len(scored_docs)}")
    for doc, score in filtered_docs:
        filename = doc.metadata.get('filename', 'unknown')
        print(f"  - {filename}: {score:.3f}")

    print("\n=== Test Complete ===")

def test_convenience_function():
    """Test the convenience function"""

    print("\n=== Testing Convenience Function ===")

    query = "machine learning guide"
    documents = create_test_documents()
    similarity_scores = [0.9, 0.7, 0.5]

    # Use convenience function
    results = score_documents(query, documents, similarity_scores, threshold=0.3)

    print(f"Results from convenience function: {len(results)} documents")
    for doc, score in results:
        filename = doc.metadata.get('filename', 'unknown')
        print(f"  - {filename}: {score:.3f}")

if __name__ == "__main__":
    try:
        test_scoring_service()
        test_convenience_function()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required dependencies: pip install scikit-learn numpy")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)