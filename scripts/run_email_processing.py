#!/usr/bin/env python3
"""
Email Processing Runner Script

This script runs the complete email processing pipeline:
1. Generates test emails and saves them to files
2. Sends emails to Redis queue
3. Processes emails through Celery workers
4. Monitors processing results
"""

import sys
import os
import json
import time
import redis
from pathlib import Path
import structlog
from typing import List, Dict, Any

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import EmailInput
from app.services.email_processor import EmailProcessor
from app.database.dynamodb import DynamoDBService
from scripts.generate_test_emails import EmailGenerator

logger = structlog.get_logger()


class EmailProcessingRunner:
    """Runner for the complete email processing pipeline."""
    
    def __init__(self):
        """Initialize the processing runner."""
        self.redis_client = redis.from_url(settings.redis_url)
        self.email_processor = EmailProcessor()
        self.db_service = DynamoDBService()
        self.email_generator = EmailGenerator()
    
    def run_complete_pipeline(self):
        """Run the complete email processing pipeline."""
        print("🚀 Starting Complete Email Processing Pipeline")
        print("=" * 60)
        
        # Step 1: Generate and save test emails
        print("\n📧 Step 1: Generating Test Emails")
        file_paths, sent_count = self.email_generator.run()
        
        # Step 2: Process emails directly (without Celery for testing)
        print("\n⚙️  Step 2: Processing Emails")
        self.process_emails_directly()
        
        # Step 3: Display results
        print("\n📊 Step 3: Processing Results")
        self.display_results()
        
        # Step 4: Database statistics
        print("\n📈 Step 4: Database Statistics")
        self.display_database_stats()
        
        print("\n✅ Pipeline completed successfully!")
    
    def process_emails_directly(self):
        """Process emails directly without Celery for testing."""
        # Read emails from test_data directory
        test_data_dir = Path("test_data")
        
        if not test_data_dir.exists():
            print("❌ No test data directory found")
            return
        
        email_files = list(test_data_dir.glob("*.json"))
        
        if not email_files:
            print("❌ No email files found in test_data directory")
            return
        
        print(f"📁 Found {len(email_files)} email files to process")
        
        processed_results = []
        
        for i, email_file in enumerate(email_files, 1):
            try:
                print(f"\n🔄 Processing email {i}/{len(email_files)}: {email_file.name}")
                
                # Load email data
                with open(email_file, 'r', encoding='utf-8') as f:
                    email_data = json.load(f)
                
                # Create EmailInput instance
                email_input = EmailInput(**email_data)
                
                # Process email
                start_time = time.time()
                result = self.email_processor.process_email(email_input)
                processing_time = time.time() - start_time
                
                # Store result in database
                doc_id = self.db_service.store_result(result)
                
                processed_results.append({
                    'file': email_file.name,
                    'doc_id': doc_id,
                    'category': result.email_category.value,
                    'business': result.business_entity.name,
                    'confidence': result.confidence_score,
                    'processing_time': processing_time,
                    'sender_domain': result.metadata.sender_domain if result.metadata else 'unknown'
                })
                
                print(f"  ✅ Category: {result.email_category.value}")
                print(f"  🏢 Business: {result.business_entity.name}")
                print(f"  📊 Confidence: {result.confidence_score:.3f}")
                print(f"  ⏱️  Time: {processing_time:.2f}s")
                
            except Exception as exc:
                print(f"  ❌ Error processing {email_file.name}: {exc}")
                logger.error("Email processing failed", file=email_file.name, error=str(exc))
        
        self.processed_results = processed_results
        return processed_results
    
    def display_results(self):
        """Display processing results summary."""
        if not hasattr(self, 'processed_results') or not self.processed_results:
            print("❌ No processing results available")
            return
        
        results = self.processed_results
        
        print(f"📊 Processed {len(results)} emails")
        print("\n📈 Results Summary:")
        
        # Category distribution
        categories = {}
        confidences = []
        processing_times = []
        
        for result in results:
            category = result['category']
            categories[category] = categories.get(category, 0) + 1
            confidences.append(result['confidence'])
            processing_times.append(result['processing_time'])
        
        print("\n🏷️  Category Distribution:")
        for category, count in sorted(categories.items()):
            percentage = (count / len(results)) * 100
            print(f"  {category}: {count} ({percentage:.1f}%)")
        
        print(f"\n📊 Confidence Scores:")
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        print(f"  Average: {avg_confidence:.3f}")
        print(f"  Range: {min_confidence:.3f} - {max_confidence:.3f}")
        
        print(f"\n⏱️  Processing Times:")
        avg_time = sum(processing_times) / len(processing_times)
        min_time = min(processing_times)
        max_time = max(processing_times)
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Range: {min_time:.2f}s - {max_time:.2f}s")
        
        # High confidence results
        high_confidence = [r for r in results if r['confidence'] > 0.8]
        print(f"\n🎯 High Confidence Results (>0.8): {len(high_confidence)}/{len(results)}")
        
        for result in high_confidence:
            print(f"  📧 {result['file']}: {result['category']} ({result['confidence']:.3f})")
    
    def display_database_stats(self):
        """Display database statistics."""
        try:
            # DynamoDB stats
            dynamo_stats = self.db_service.get_statistics()
            print("🗄️  DynamoDB Statistics:")
            print(f"  Total Results: {dynamo_stats.get('total_results', 0)}")
            print(f"  Sample Size: {dynamo_stats.get('sample_size', 0)}")
            print(f"  Average Confidence: {dynamo_stats.get('average_confidence', 0):.3f}")
            
            categories = dynamo_stats.get('category_distribution', {})
            if categories:
                print("  Category Distribution:")
                for category, count in categories.items():
                    print(f"    {category}: {count}")
            
            domains = dynamo_stats.get('top_domains', {})
            if domains:
                print("  Top Domains:")
                for domain, count in list(domains.items())[:5]:
                    print(f"    {domain}: {count}")
            
            # Vector DB stats
            vector_stats = self.email_processor.vector_store.get_collection_stats()
            print(f"\n🔍 Vector Database Statistics:")
            print(f"  Total Documents: {vector_stats.get('total_documents', 0)}")
            print(f"  Unique Domains: {len(vector_stats.get('domains', []))}")
            print(f"  Categories: {', '.join(vector_stats.get('categories', []))}")
            print(f"  Industries: {len(vector_stats.get('industries', []))}")
            
        except Exception as exc:
            print(f"❌ Error getting database stats: {exc}")
            logger.error("Failed to get database stats", error=str(exc))
    
    def test_vector_similarity(self):
        """Test vector similarity search with sample queries."""
        print("\n🔍 Testing Vector Similarity Search")
        print("-" * 40)
        
        test_queries = [
            {
                "content": "Black Friday sale with 50% discount",
                "domain": "shop.com",
                "expected": "marketing"
            },
            {
                "content": "Order confirmation payment receipt",
                "domain": "store.com", 
                "expected": "transactional"
            },
            {
                "content": "Please complete our customer survey",
                "domain": "feedback.com",
                "expected": "survey"
            }
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                from app.models import EmailMetadata
                
                metadata = EmailMetadata(
                    sender_domain=query["domain"],
                    urls=[],
                    footer_text=None
                )
                
                # Search for similar emails
                matches = self.email_processor.vector_store.search_similar_emails(
                    query["content"], metadata, n_results=3
                )
                
                print(f"\n🔍 Query {i}: '{query['content'][:30]}...'")
                print(f"  Expected: {query['expected']}")
                print(f"  Found {len(matches)} matches:")
                
                for j, match in enumerate(matches, 1):
                    similarity = match.get('similarity', 0)
                    match_metadata = match.get('metadata', {})
                    category = match_metadata.get('email_category', 'unknown')
                    domain = match_metadata.get('sender_domain', 'unknown')
                    
                    print(f"    {j}. {category} from {domain} (similarity: {similarity:.3f})")
                
            except Exception as exc:
                print(f"  ❌ Error in similarity search: {exc}")
    
    def cleanup_test_data(self):
        """Clean up test data and reset databases."""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Clear Redis queue
            queue_length = self.redis_client.llen("email_processing")
            if queue_length > 0:
                self.redis_client.delete("email_processing")
                print(f"  ✅ Cleared {queue_length} items from Redis queue")
            
            # Reset vector database
            if hasattr(self.email_processor, 'vector_store'):
                self.email_processor.vector_store.reset_collection()
                print("  ✅ Reset vector database")
            
            print("  ✅ Cleanup completed")
            
        except Exception as exc:
            print(f"  ❌ Cleanup error: {exc}")


def main():
    """Main function to run the email processing pipeline."""
    runner = EmailProcessingRunner()
    
    try:
        # Run complete pipeline
        runner.run_complete_pipeline()
        
        # Test vector similarity
        runner.test_vector_similarity()
        
        # Optional: cleanup (uncomment if needed)
        # runner.cleanup_test_data()
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as exc:
        print(f"\n❌ Pipeline failed: {exc}")
        logger.error("Pipeline execution failed", error=str(exc))


if __name__ == "__main__":
    main()
