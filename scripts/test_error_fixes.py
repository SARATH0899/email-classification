#!/usr/bin/env python3
"""
Test Error Fixes

This script tests all the error fixes for:
1. LLM classification with fallback
2. Presidio configuration warnings
3. Embeddings connection issues
4. PII anonymization parameters
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from app.llm.models import LLMModelManager
from app.processing.pii_processor import PIIProcessor
from app.database.vector_store import VectorStoreService
from app.services.similarity_matcher import SimilarityMatcher

logger = structlog.get_logger()


def test_llm_models():
    """Test LLM model initialization with fallback."""
    print("🤖 Testing LLM Models with Fallback")
    print("=" * 40)
    
    try:
        # Initialize model manager
        print("📋 Initializing LLM model manager...")
        model_manager = LLMModelManager()
        
        # Test getting primary model
        print("🔍 Testing primary model retrieval...")
        primary_model = model_manager.get_model('primary')
        print(f"✅ Primary model: {type(primary_model).__name__}")
        
        # Test available models
        available_models = model_manager.get_available_models()
        print(f"📊 Available models: {available_models}")
        
        # Test model info
        if available_models:
            model_info = model_manager.get_model_info(available_models[0])
            print(f"ℹ️  Model info: {model_info}")
        
        return True
        
    except Exception as exc:
        print(f"❌ LLM models test failed: {exc}")
        logger.error("LLM models test failed", error=str(exc))
        return False


def test_presidio_configuration():
    """Test Presidio configuration loading."""
    print(f"\n🔒 Testing Presidio Configuration")
    print("-" * 40)
    
    try:
        # Initialize PII processor
        print("📋 Initializing PII processor...")
        pii_processor = PIIProcessor()
        
        # Test configuration loading
        print(f"✅ Configuration loaded: {bool(pii_processor.config)}")
        print(f"📊 NLP engine: {pii_processor.config.get('nlp_engine_name', 'unknown')}")
        
        # Check for NER configuration
        has_ner_config = 'ner_model_configuration' in pii_processor.config
        print(f"🧠 Has NER config: {has_ner_config}")
        
        if has_ner_config:
            ner_config = pii_processor.config['ner_model_configuration']
            print(f"🗺️  Entity mappings: {len(ner_config.get('model_to_presidio_entity_mapping', {}))}")
            print(f"📉 Low score entities: {len(ner_config.get('low_score_entity_names', []))}")
            print(f"🚫 Labels to ignore: {ner_config.get('labels_to_ignore', [])}")
        
        # Test basic PII detection
        test_text = "Contact John Doe at john.doe@example.com"
        print(f"\n🧪 Testing PII detection...")
        entities = pii_processor.detect_pii(test_text)
        print(f"✅ Detected {len(entities)} entities")
        
        # Test anonymization
        print(f"🔒 Testing text anonymization...")
        anonymized = pii_processor.anonymize_text(test_text)
        print(f"✅ Anonymization successful: {len(anonymized)} chars")
        
        return True
        
    except Exception as exc:
        print(f"❌ Presidio configuration test failed: {exc}")
        logger.error("Presidio test failed", error=str(exc))
        return False


def test_embeddings_fallback():
    """Test embeddings initialization with fallback."""
    print(f"\n🔍 Testing Embeddings with Fallback")
    print("-" * 40)
    
    try:
        # Initialize vector store
        print("📋 Initializing vector store...")
        vector_store = VectorStoreService()
        
        # Test embeddings
        print(f"✅ Embeddings type: {type(vector_store.embeddings).__name__}")
        
        # Test embedding generation
        test_text = "This is a test email about marketing products."
        print(f"🧪 Testing embedding generation...")
        embedding = vector_store.embeddings.embed_query(test_text)
        print(f"✅ Generated embedding: {len(embedding)} dimensions")
        
        # Test collection info
        collection_count = vector_store.collection.count()
        print(f"📊 Collection count: {collection_count}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Embeddings test failed: {exc}")
        logger.error("Embeddings test failed", error=str(exc))
        return False


def test_similarity_matcher():
    """Test similarity matcher with error handling."""
    print(f"\n🔗 Testing Similarity Matcher")
    print("-" * 40)
    
    try:
        # Initialize similarity matcher
        print("📋 Initializing similarity matcher...")
        similarity_matcher = SimilarityMatcher()
        
        # Check if vector store is available
        has_vector_store = similarity_matcher.vector_store is not None
        print(f"✅ Vector store available: {has_vector_store}")
        
        if has_vector_store:
            # Test similarity search
            from app.models import EmailMetadata
            
            test_content = "This is a marketing email about special offers."
            test_metadata = EmailMetadata(
                sender_domain="example.com",
                footer_text=None,
                urls=[]
            )
            
            print(f"🔍 Testing similarity search...")
            match = similarity_matcher.find_best_match(test_content, test_metadata)
            print(f"✅ Similarity search completed: {match is not None}")
        else:
            print("⚠️  Vector store not available, skipping similarity search")
        
        return True
        
    except Exception as exc:
        print(f"❌ Similarity matcher test failed: {exc}")
        logger.error("Similarity matcher test failed", error=str(exc))
        return False


def test_email_classification():
    """Test email classification with fallback."""
    print(f"\n📧 Testing Email Classification")
    print("-" * 40)
    
    try:
        from app.llm.chains import EmailClassificationChain
        from app.models import EmailMetadata
        
        # Initialize classification chain
        print("📋 Initializing email classification chain...")
        classifier = EmailClassificationChain()
        
        # Test classification
        test_content = "Thank you for your purchase. Your order #12345 has been confirmed."
        test_metadata = EmailMetadata(
            sender_domain="shop.example.com",
            footer_text="Unsubscribe here",
            urls=["https://shop.example.com/order/12345"]
        )
        
        print(f"🧪 Testing email classification...")
        result = classifier.classify_email(test_content, test_metadata)
        
        print(f"✅ Classification successful:")
        print(f"  Category: {result.email_category.value}")
        print(f"  Business: {result.business_entity.name}")
        print(f"  Confidence: {result.confidence_score}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Email classification test failed: {exc}")
        logger.error("Email classification test failed", error=str(exc))
        return False


def main():
    """Main function."""
    print("🧪 Error Fixes Testing")
    print("=" * 50)
    
    tests = [
        ("LLM Models", test_llm_models),
        ("Presidio Configuration", test_presidio_configuration),
        ("Embeddings Fallback", test_embeddings_fallback),
        ("Similarity Matcher", test_similarity_matcher),
        ("Email Classification", test_email_classification),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as exc:
            print(f"❌ {test_name} failed with exception: {exc}")
            results[test_name] = False
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All error fixes working correctly!")
        print("\n💡 The system should now handle connection failures gracefully.")
    else:
        print("❌ Some tests failed. Check the logs for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
