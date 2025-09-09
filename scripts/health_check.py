#!/usr/bin/env python3
"""
Health Check Script

This script performs a comprehensive health check of the application.
"""

import sys
import os
import time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_imports():
    """Check if all imports work."""
    print("🔍 Checking imports...")
    try:
        from scripts.test_imports import test_imports
        return test_imports()
    except Exception as e:
        print(f"❌ Import check failed: {e}")
        return False

def check_redis_connection():
    """Check Redis connection."""
    print("🔍 Checking Redis connection...")
    try:
        import redis
        from app.config import settings
        
        client = redis.from_url(settings.redis_url)
        client.ping()
        print("  ✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        return False

def check_dynamodb_connection():
    """Check DynamoDB connection."""
    print("🔍 Checking DynamoDB connection...")
    try:
        from app.database.dynamodb import DynamoDBService
        
        db_service = DynamoDBService()
        # Try to get statistics (this will test the connection)
        stats = db_service.get_statistics()
        print("  ✅ DynamoDB connection successful")
        return True
    except Exception as e:
        print(f"  ❌ DynamoDB connection failed: {e}")
        return False

def check_llm_configuration():
    """Check LLM configuration."""
    print("🔍 Checking LLM configuration...")
    try:
        from app.config import settings
        from app.llm.models import model_manager
        
        provider = settings.llm_provider
        print(f"  📋 LLM Provider: {provider}")
        
        # Try to get a model
        model = model_manager.get_model('primary')
        print(f"  ✅ LLM model loaded successfully")
        return True
    except Exception as e:
        print(f"  ❌ LLM configuration failed: {e}")
        return False

def check_vector_store():
    """Check vector store."""
    print("🔍 Checking vector store...")
    try:
        from app.database.vector_store import VectorStoreService
        
        vector_service = VectorStoreService()
        stats = vector_service.get_collection_stats()
        print(f"  ✅ Vector store initialized (documents: {stats.get('total_documents', 0)})")
        return True
    except Exception as e:
        print(f"  ❌ Vector store failed: {e}")
        return False

def run_health_check():
    """Run comprehensive health check."""
    print("🏥 Running Health Check")
    print("=" * 40)
    
    checks = [
        ("Imports", check_imports),
        ("Redis", check_redis_connection),
        ("DynamoDB", check_dynamodb_connection),
        ("LLM Configuration", check_llm_configuration),
        ("Vector Store", check_vector_store),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"  ❌ {check_name} check failed: {e}")
            results[check_name] = False
    
    # Summary
    print("\n📊 Health Check Summary")
    print("=" * 40)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ All health checks passed!")
        return True
    else:
        print("❌ Some health checks failed!")
        return False

def main():
    """Main function."""
    try:
        success = run_health_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Health check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
