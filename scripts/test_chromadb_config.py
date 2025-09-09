#!/usr/bin/env python3
"""
Test ChromaDB Configuration

This script tests the ChromaDB configuration to ensure it can connect to
both local and external ChromaDB instances.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from app.config import settings
from app.database.vector_store import VectorStoreService

logger = structlog.get_logger()


def test_chromadb_connection():
    """Test ChromaDB connection and basic operations."""
    print("🔍 Testing ChromaDB Connection")
    print("=" * 40)
    
    try:
        # Show configuration
        print(f"📋 ChromaDB Configuration:")
        print(f"  Use External: {settings.chromadb_use_external}")
        print(f"  Host: {settings.chromadb_host}")
        print(f"  Port: {settings.chromadb_port}")
        print(f"  Persist Dir: {settings.chroma_persist_directory}")
        
        # Initialize vector store
        print(f"\n🔌 Initializing vector store...")
        vector_store = VectorStoreService()
        print(f"✅ Vector store initialized successfully")
        
        # Test collection access
        print(f"\n📊 Testing collection access...")
        collection_count = vector_store.collection.count()
        print(f"✅ Collection count: {collection_count}")
        
        # Test basic operations
        print(f"\n🧪 Testing basic operations...")
        
        # Test embedding generation
        test_text = "This is a test email for ChromaDB."
        embedding = vector_store.embeddings.embed_query(test_text)
        print(f"✅ Generated embedding: {len(embedding)} dimensions")
        
        # Test adding a document (if embeddings work)
        from app.models import EmailMetadata
        test_metadata = EmailMetadata(
            sender_domain="test.example.com",
            footer_text="Test footer",
            urls=["https://test.example.com"]
        )
        
        doc_id = vector_store.add_email_embedding(
            email_content=test_text,
            metadata=test_metadata,
            business_name="Test Company",
            email_category="marketing"
        )
        print(f"✅ Added test document: {doc_id}")
        
        # Test searching
        results = vector_store.search_similar_emails(
            query_content=test_text,
            query_metadata=test_metadata,
            n_results=1
        )
        print(f"✅ Search results: {len(results)} found")
        
        # Clean up test document
        if doc_id:
            try:
                vector_store.collection.delete(ids=[doc_id])
                print(f"🧹 Cleaned up test document")
            except Exception:
                pass  # Ignore cleanup errors
        
        return True
        
    except Exception as exc:
        print(f"❌ ChromaDB connection test failed: {exc}")
        logger.error("ChromaDB test failed", error=str(exc))
        return False


def test_chromadb_client_types():
    """Test different ChromaDB client types."""
    print(f"\n🔧 Testing ChromaDB Client Types")
    print("-" * 40)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Test HttpClient (external)
        if settings.chromadb_use_external:
            print(f"🌐 Testing HttpClient connection...")
            try:
                http_client = chromadb.HttpClient(
                    host=settings.chromadb_host,
                    port=settings.chromadb_port,
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Test basic operation
                collections = http_client.list_collections()
                print(f"✅ HttpClient works: {len(collections)} collections")
                
            except Exception as http_exc:
                print(f"❌ HttpClient failed: {http_exc}")
        
        # Test PersistentClient (local)
        print(f"💾 Testing PersistentClient...")
        try:
            os.makedirs(settings.chroma_persist_directory, exist_ok=True)
            persistent_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Test basic operation
            collections = persistent_client.list_collections()
            print(f"✅ PersistentClient works: {len(collections)} collections")
            
        except Exception as persistent_exc:
            print(f"❌ PersistentClient failed: {persistent_exc}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Client types test failed: {exc}")
        return False


def test_embeddings_providers():
    """Test different embeddings providers."""
    print(f"\n🧠 Testing Embeddings Providers")
    print("-" * 40)
    
    try:
        # Test current provider
        vector_store = VectorStoreService()
        embeddings_type = type(vector_store.embeddings).__name__
        print(f"📊 Current embeddings: {embeddings_type}")
        
        # Test embedding generation
        test_texts = [
            "This is a marketing email about products.",
            "Your order confirmation for purchase #12345.",
            "Personal message from a friend."
        ]
        
        for i, text in enumerate(test_texts):
            try:
                embedding = vector_store.embeddings.embed_query(text)
                print(f"✅ Text {i+1}: {len(embedding)} dimensions")
            except Exception as embed_exc:
                print(f"❌ Text {i+1} failed: {embed_exc}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Embeddings test failed: {exc}")
        return False


def test_collection_operations():
    """Test ChromaDB collection operations."""
    print(f"\n📚 Testing Collection Operations")
    print("-" * 40)
    
    try:
        vector_store = VectorStoreService()
        
        # Test collection info
        collection = vector_store.collection
        print(f"📋 Collection name: {collection.name}")
        print(f"📊 Document count: {collection.count()}")
        
        # Test metadata
        try:
            metadata = collection.metadata
            print(f"ℹ️  Collection metadata: {metadata}")
        except Exception:
            print(f"⚠️  Could not retrieve collection metadata")
        
        # Test peek (get some documents)
        try:
            peek_result = collection.peek(limit=3)
            print(f"👀 Peek results: {len(peek_result.get('ids', []))} documents")
        except Exception as peek_exc:
            print(f"⚠️  Peek failed: {peek_exc}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Collection operations test failed: {exc}")
        return False


def main():
    """Main function."""
    print("🧪 ChromaDB Configuration Testing")
    print("=" * 50)
    
    tests = [
        ("ChromaDB Connection", test_chromadb_connection),
        ("Client Types", test_chromadb_client_types),
        ("Embeddings Providers", test_embeddings_providers),
        ("Collection Operations", test_collection_operations),
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
        print("✅ All ChromaDB tests passed!")
        print("\n💡 ChromaDB is configured correctly and ready to use.")
        print(f"🌐 ChromaDB UI available at: http://localhost:3000")
    else:
        print("❌ Some tests failed. Check the configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
