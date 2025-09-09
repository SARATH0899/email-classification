#!/usr/bin/env python3
"""
Test PII Configuration

This script tests the PII processor configuration to ensure SpaCy and Presidio
are properly configured and working without warnings.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from app.processing.pii_processor import PIIProcessor

logger = structlog.get_logger()


def test_pii_configuration():
    """Test PII processor configuration and functionality."""
    print("🔍 Testing PII Configuration")
    print("=" * 40)
    
    try:
        # Initialize PII processor
        print("📋 Initializing PII processor...")
        pii_processor = PIIProcessor()
        print("✅ PII processor initialized successfully")
        
        # Test text with various PII types
        test_text = """
        Hello John Doe,
        
        Please contact me at john.doe@example.com or call (555) 123-4567.
        My credit card number is 4532-1234-5678-9012.
        
        Best regards,
        Jane Smith
        ABC Corporation
        123 Main Street, New York, NY 10001
        """
        
        print(f"\n📧 Testing with sample text:")
        print(f"Text length: {len(test_text)} characters")
        
        # Test PII detection
        print("\n🔍 Testing PII detection...")
        pii_entities = pii_processor.detect_pii(test_text)
        print(f"✅ Detected {len(pii_entities)} PII entities:")
        
        for entity in pii_entities:
            print(f"  - {entity['entity_type']}: '{entity['text']}' (score: {entity['score']:.3f})")
        
        # Test PII extraction
        print("\n📊 Testing PII data extraction...")
        extracted_data = pii_processor.extract_pii_data(test_text)
        print("✅ Extracted PII data:")
        
        for data_type, values in extracted_data.items():
            if values:
                print(f"  - {data_type}: {values}")
        
        # Test anonymization
        print("\n🔒 Testing text anonymization...")
        anonymized_text = pii_processor.anonymize_text(test_text)
        print("✅ Text anonymized successfully")
        print(f"Original length: {len(test_text)}")
        print(f"Anonymized length: {len(anonymized_text)}")
        
        # Show a sample of anonymized text
        print(f"\nSample anonymized text:")
        print(anonymized_text[:200] + "..." if len(anonymized_text) > 200 else anonymized_text)
        
        # Test entity statistics
        print("\n📈 Testing entity statistics...")
        stats = pii_processor.get_entity_statistics(test_text)
        print("✅ Entity statistics:")
        
        for entity_type, count in stats.items():
            print(f"  - {entity_type}: {count}")
        
        print(f"\n🎉 All PII tests completed successfully!")
        return True
        
    except Exception as exc:
        print(f"❌ PII configuration test failed: {exc}")
        logger.error("PII configuration test failed", error=str(exc))
        return False


def test_spacy_model():
    """Test SpaCy model loading."""
    print(f"\n🧠 Testing SpaCy Model")
    print("-" * 30)
    
    try:
        import spacy
        
        # Test loading the model
        print("📋 Loading SpaCy model...")
        nlp = spacy.load("en_core_web_sm")
        print("✅ SpaCy model loaded successfully")
        
        # Test basic NLP processing
        test_text = "John Doe works at ABC Corporation in New York."
        doc = nlp(test_text)
        
        print(f"\n📝 Testing NLP processing:")
        print(f"Text: {test_text}")
        print(f"Entities found: {len(doc.ents)}")
        
        for ent in doc.ents:
            print(f"  - {ent.text}: {ent.label_}")
        
        return True
        
    except Exception as exc:
        print(f"❌ SpaCy model test failed: {exc}")
        return False


def test_presidio_engines():
    """Test Presidio engines directly."""
    print(f"\n🔒 Testing Presidio Engines")
    print("-" * 30)
    
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        
        # Test analyzer
        print("📋 Initializing Presidio analyzer...")
        analyzer = AnalyzerEngine()
        print("✅ Presidio analyzer initialized")
        
        # Test anonymizer
        print("📋 Initializing Presidio anonymizer...")
        anonymizer = AnonymizerEngine()
        print("✅ Presidio anonymizer initialized")
        
        # Test basic analysis
        test_text = "Contact John at john@example.com"
        results = analyzer.analyze(text=test_text, entities=['EMAIL_ADDRESS', 'PERSON'], language='en')
        
        print(f"\n📊 Analysis results:")
        print(f"Text: {test_text}")
        print(f"Entities found: {len(results)}")
        
        for result in results:
            print(f"  - {result.entity_type}: {test_text[result.start:result.end]} (score: {result.score:.3f})")
        
        return True
        
    except Exception as exc:
        print(f"❌ Presidio engines test failed: {exc}")
        return False


def main():
    """Main function."""
    print("🧪 PII Configuration Testing")
    print("=" * 50)
    
    tests = [
        ("SpaCy Model", test_spacy_model),
        ("Presidio Engines", test_presidio_engines),
        ("PII Configuration", test_pii_configuration),
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
        print("✅ All PII configuration tests passed!")
        print("\n💡 The PII processor should now work without warnings.")
    else:
        print("❌ Some tests failed. Check the configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
