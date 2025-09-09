#!/usr/bin/env python3
"""
Import Testing Script

This script tests all imports to ensure they work correctly.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all critical imports."""
    print("🧪 Testing imports...")
    
    try:
        print("  ✓ Testing app.config...")
        from app.config import settings
        
        print("  ✓ Testing app.models...")
        from app.models import EmailInput, EmailCategory, ProcessedEmail
        
        print("  ✓ Testing app.database...")
        from app.database.dynamodb import DynamoDBService
        from app.database.vector_store import VectorStoreService
        
        print("  ✓ Testing app.llm...")
        from app.llm.models import model_manager
        from app.llm.chains import EmailClassificationChain
        
        print("  ✓ Testing app.processing...")
        from app.processing.html_processor import HTMLProcessor
        from app.processing.pii_processor import PIIProcessor
        
        print("  ✓ Testing app.services...")
        from app.services.email_processor import EmailProcessor
        from app.services.metadata_extractor import MetadataExtractor
        from app.services.similarity_matcher import SimilarityMatcher
        
        print("  ✓ Testing app.prompts...")
        from app.prompts import email_classification, dpo_extraction
        
        print("  ✓ Testing app.tasks...")
        from app.tasks import process_email_task
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
