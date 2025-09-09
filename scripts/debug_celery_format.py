#!/usr/bin/env python3
"""
Debug Celery Message Format

This script creates a real Celery task and examines the exact message format
that gets created, so we can match it exactly in the Go service.
"""

import sys
import os
import json
import redis
import structlog
from uuid import uuid4

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.tasks import process_email_task

logger = structlog.get_logger()


def debug_real_celery_message():
    """Create a real Celery message and examine its structure."""
    print("🔍 Debugging Real Celery Message Format")
    print("=" * 50)
    
    # Connect to Redis
    redis_client = redis.from_url(settings.redis_url)
    queue_name = "debug_queue"
    
    # Clear the queue
    redis_client.delete(queue_name)
    
    # Create a task using Celery's apply_async with custom queue
    test_filename = "email_01_marketing_shopify_com.json"
    print(f"📧 Creating real Celery task for: {test_filename}")
    
    # Queue the task to our debug queue
    result = process_email_task.apply_async(
        args=[test_filename],
        queue=queue_name
    )
    print(f"✅ Task queued with ID: {result.id}")
    
    # Get the raw message from Redis
    raw_message = redis_client.rpop(queue_name)
    if raw_message:
        try:
            message_str = raw_message.decode('utf-8')
            message_data = json.loads(message_str)
            
            print("\n📋 Complete Real Celery Message:")
            print(json.dumps(message_data, indent=2))
            
            # Examine the body specifically
            if 'body' in message_data:
                print("\n📦 Message Body (raw):")
                print(f"Body type: {type(message_data['body'])}")
                print(f"Body content: {message_data['body']}")
                
                try:
                    body_data = json.loads(message_data['body'])
                    print(f"\n📦 Parsed Body:")
                    print(f"Body type after parsing: {type(body_data)}")
                    print(f"Body length: {len(body_data) if isinstance(body_data, (list, tuple)) else 'N/A'}")
                    print(json.dumps(body_data, indent=2))
                    
                    if isinstance(body_data, list):
                        print(f"\n🔍 Body Elements:")
                        for i, element in enumerate(body_data):
                            print(f"  Element {i}: {type(element)} = {element}")
                            
                except json.JSONDecodeError as e:
                    print(f"❌ Body is not JSON: {e}")
            
            # Examine headers
            if 'headers' in message_data:
                print(f"\n📋 Headers:")
                for key, value in message_data['headers'].items():
                    print(f"  {key}: {type(value)} = {value}")
            
            # Examine properties
            if 'properties' in message_data:
                print(f"\n🏷️  Properties:")
                for key, value in message_data['properties'].items():
                    print(f"  {key}: {type(value)} = {value}")
                    
        except Exception as e:
            print(f"❌ Failed to parse message: {e}")
            print(f"Raw message: {raw_message}")
    else:
        print("❌ No message found in queue")
    
    # Clean up
    redis_client.delete(queue_name)


def create_minimal_test_message():
    """Create the minimal message format that should work."""
    print(f"\n🔧 Creating Minimal Test Message")
    print("-" * 30)
    
    task_id = str(uuid4())
    test_filename = "email_01_marketing_shopify_com.json"
    
    # Try the simplest possible format first
    simple_body = [
        [test_filename],  # args
        {},              # kwargs
        {}               # embed (minimal)
    ]
    
    minimal_message = {
        "body": json.dumps(simple_body),
        "headers": {
            "lang": "py",
            "task": "app.tasks.process_email_task",
            "id": task_id,
            "root_id": task_id,
            "parent_id": None,
            "group": None,
            "retries": 0,
            "timelimit": [None, None],
            "argsrepr": f"('{test_filename}',)",
            "kwargsrepr": "{}",
            "origin": "gen1@go-email-queue",
        },
        "properties": {
            "correlation_id": task_id,
            "content_type": "application/json",
            "content_encoding": "utf-8",
            "delivery_tag": 1,
            "delivery_mode": 2,
            "priority": 0,
            "delivery_info": {
                "exchange": "",
                "routing_key": "celery",
            },
        },
    }
    
    print("📋 Minimal Message Format:")
    print(json.dumps(minimal_message, indent=2))
    
    # Test this format
    redis_client = redis.from_url(settings.redis_url)
    test_queue = "minimal_test"
    
    redis_client.lpush(test_queue, json.dumps(minimal_message))
    print(f"✅ Pushed minimal message to {test_queue}")
    
    # Retrieve and verify
    retrieved = redis_client.rpop(test_queue)
    if retrieved:
        retrieved_data = json.loads(retrieved.decode('utf-8'))
        body_data = json.loads(retrieved_data['body'])
        print(f"✅ Retrieved message body has {len(body_data)} elements")
        print(f"   Args: {body_data[0]}")
        print(f"   Kwargs: {body_data[1]}")
        print(f"   Embed: {body_data[2]}")
    
    redis_client.delete(test_queue)


def main():
    """Main function."""
    try:
        debug_real_celery_message()
        create_minimal_test_message()
        
        print("\n💡 Next Steps:")
        print("1. Compare the real Celery message with our Go format")
        print("2. Adjust Go service to match the exact structure")
        print("3. Pay special attention to the body format and element count")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        logger.error("Celery format debug failed", error=str(e))


if __name__ == "__main__":
    main()
