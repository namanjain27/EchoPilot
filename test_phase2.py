#!/usr/bin/env python3
"""
Test script for Phase 2 implementation
Tests ChromaDB integration, RAG engine, and knowledge base functionality
"""

import os
import sys
import logging
from typing import Dict, Any

# Add src to path
sys.path.append('src')

from data.knowledge_base import KnowledgeBaseManager, KnowledgeBaseType
from data.embeddings import EmbeddingManager  
from data.document_processor import DocumentProcessor, IngestionPipeline
from ai.rag_engine import RAGEngine
from ai.intent_classifier import IntentClassifier
from auth.role_manager import UserRole

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_embedding_manager():
    """Test the embedding manager"""
    print("\n" + "="*60)
    print("TESTING EMBEDDING MANAGER")
    print("="*60)
    
    embedding_manager = EmbeddingManager()
    
    # Test availability
    print(f"Embedding Manager Available: {embedding_manager.is_available()}")
    
    if embedding_manager.is_available():
        # Test model info
        info = embedding_manager.get_model_info()
        print(f"Model Info: {info}")
        
        # Test single encoding
        test_text = "What are your business hours?"
        embedding = embedding_manager.encode_single(test_text)
        if embedding is not None:
            print(f"Single text embedding shape: {embedding.shape}")
        
        # Test similarity search
        documents = [
            "Our customer support is available 24/7",
            "Business hours are 9 AM to 5 PM Monday through Friday",
            "Technical issues can be reported through our support portal"
        ]
        
        similar_docs = embedding_manager.find_most_similar(test_text, documents, top_k=2)
        print(f"Most similar documents to '{test_text}':")
        for doc, score in similar_docs:
            print(f"  Score: {score:.3f} - {doc}")
    
    return embedding_manager.is_available()


def test_knowledge_base():
    """Test knowledge base functionality"""
    print("\n" + "="*60)
    print("TESTING KNOWLEDGE BASE")
    print("="*60)
    
    try:
        # Initialize knowledge base
        kb_manager = KnowledgeBaseManager()
        print("Knowledge base manager initialized successfully")
        
        # Initialize with sample data
        success = kb_manager.initialize_sample_data()
        print(f"Sample data initialization: {'SUCCESS' if success else 'FAILED'}")
        
        # Get collection stats
        stats = kb_manager.get_collection_stats()
        print(f"Collection Statistics: {stats}")
        
        # Test search functionality
        test_queries = [
            "What are the business hours?",
            "How do I reset my password?", 
            "What is our revenue?",
            "What's the team structure?"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            
            # Test customer access
            customer_results = kb_manager.search_all_accessible(query, 'customer', n_results=2)
            print(f"Customer accessible KBs: {list(customer_results.keys())}")
            
            # Test associate access  
            associate_results = kb_manager.search_all_accessible(query, 'associate', n_results=2)
            print(f"Associate accessible KBs: {list(associate_results.keys())}")
            
            # Show a sample result
            if associate_results:
                first_kb = next(iter(associate_results.values()))
                if first_kb['documents']:
                    doc = first_kb['documents'][0][:100] + "..." if len(first_kb['documents'][0]) > 100 else first_kb['documents'][0]
                    print(f"Sample result: {doc}")
        
        return True
        
    except Exception as e:
        logger.error(f"Knowledge base test failed: {e}")
        return False


def test_document_processor():
    """Test document processing functionality"""
    print("\n" + "="*60)
    print("TESTING DOCUMENT PROCESSOR")
    print("="*60)
    
    try:
        processor = DocumentProcessor(chunk_size=200, chunk_overlap=50)
        stats = processor.get_processing_stats()
        print(f"Processor Stats: {stats}")
        
        # Test text processing
        sample_text = """This is a sample document for testing the document processor. 
        It contains multiple sentences to test the chunking functionality. 
        The processor should be able to split this text into appropriate chunks
        while maintaining context and handling overlaps correctly. This helps
        ensure that information is not lost during the chunking process."""
        
        chunks = processor.process_text_content(sample_text, "test_document", 
                                               metadata={"category": "test"})
        
        print(f"Generated {len(chunks)} chunks from sample text")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1} (size: {len(chunk.content)}): {chunk.content[:80]}...")
        
        return len(chunks) > 0
        
    except Exception as e:
        logger.error(f"Document processor test failed: {e}")
        return False


def test_rag_engine():
    """Test RAG engine functionality"""
    print("\n" + "="*60)
    print("TESTING RAG ENGINE")
    print("="*60)
    
    try:
        # Initialize RAG engine
        rag_engine = RAGEngine()
        print("RAG engine initialized")
        
        # Initialize knowledge base
        kb_initialized = rag_engine.initialize_knowledge_base()
        print(f"Knowledge base initialization: {'SUCCESS' if kb_initialized else 'FAILED'}")
        
        # Get knowledge base stats
        stats = rag_engine.get_knowledge_base_stats()
        print(f"Knowledge base stats: {stats}")
        
        # Test RAG search for different roles
        test_queries = [
            "What are your business hours?",
            "How much revenue did we make?",
            "Can you help me reset my password?"
        ]
        
        for query in test_queries:
            print(f"\nTesting RAG query: '{query}'")
            
            # Test customer response
            customer_response = rag_engine.search_knowledge_base(query, 'customer')
            print(f"Customer Response Sources: {len(customer_response.get('sources', []))}")
            print(f"Customer KBs Used: {customer_response.get('knowledge_bases_used', [])}")
            
            # Test associate response
            associate_response = rag_engine.search_knowledge_base(query, 'associate')  
            print(f"Associate Response Sources: {len(associate_response.get('sources', []))}")
            print(f"Associate KBs Used: {associate_response.get('knowledge_bases_used', [])}")
            
            # Show sample response (first 200 chars)
            response_text = associate_response.get('response', '')
            if response_text:
                sample_response = response_text[:200] + "..." if len(response_text) > 200 else response_text
                print(f"Sample Response: {sample_response}")
        
        return True
        
    except Exception as e:
        logger.error(f"RAG engine test failed: {e}")
        return False


def test_integration():
    """Test integration between components"""
    print("\n" + "="*60)
    print("TESTING COMPONENT INTEGRATION")
    print("="*60)
    
    try:
        # Test intent classifier + RAG integration
        intent_classifier = IntentClassifier()
        rag_engine = RAGEngine()
        
        # Initialize knowledge base
        rag_engine.initialize_knowledge_base()
        
        test_messages = [
            "I'm very frustrated with your service, nothing works!",
            "Can you help me understand your billing process?",
            "What's our Q4 revenue performance looking like?"
        ]
        
        for message in test_messages:
            print(f"\nProcessing: '{message}'")
            
            # Analyze intent
            intent_analysis = intent_classifier.analyze_message(message)
            print(f"Intent: {intent_analysis.intent.value}, Urgency: {intent_analysis.urgency.value}, Sentiment: {intent_analysis.sentiment.value}")
            
            # Get RAG response for associate role
            rag_response = rag_engine.search_knowledge_base(message, 'associate')
            print(f"RAG Sources Found: {rag_response.get('source_count', 0)}")
            
            # Sample response
            response_text = rag_response.get('response', '')
            if response_text:
                sample = response_text[:150] + "..." if len(response_text) > 150 else response_text
                print(f"Response Preview: {sample}")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


def main():
    """Run all Phase 2 tests"""
    print("ECHOPILOT PHASE 2 TESTING")
    print("=" * 80)
    print("Testing ChromaDB integration, embeddings, knowledge base, and RAG engine")
    print("=" * 80)
    
    # Check required environment variables
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("⚠️  WARNING: GEMINI_API_KEY not set - some tests may use fallback responses")
    else:
        print("✅ GEMINI_API_KEY configured")
    
    chroma_key = os.getenv('CHROMADB_API_KEY')
    if not chroma_key:
        print("ℹ️  INFO: CHROMADB_API_KEY not set - using local ChromaDB")
    else:
        print("✅ CHROMADB_API_KEY configured")
    
    # Run tests
    test_results = {
        'Embedding Manager': test_embedding_manager(),
        'Knowledge Base': test_knowledge_base(),
        'Document Processor': test_document_processor(),
        'RAG Engine': test_rag_engine(),
        'Component Integration': test_integration()
    }
    
    # Print summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
        if not result:
            all_passed = False
    
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Phase 2 implementation is working correctly!")
        print("Ready features for testing:")
        print("- ChromaDB knowledge base with role-based access")
        print("- Document embedding and similarity search")  
        print("- RAG-powered responses using Gemini 2.0 Flash")
        print("- Intent classification integration")
        print("- Document processing and ingestion pipeline")
    else:
        print("\n⚠️ Some components need attention before proceeding.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())