#!/usr/bin/env python3
"""
Test Celery Queue Format

This script tests the correct format for Celery messages by creating a task
using the Python Celery client and examining the message format.
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


def test_celery_message_format():
    """Test what format Celery creates for messages."""
    print("🧪 Testing Celery Message Format")
    print("=" * 40)
    
    # Connect to Redis
    redis_client = redis.from_url(settings.redis_url)
    
    # Clear the queue first
    queue_name = "celery"
    redis_client.delete(queue_name)
    print(f"📋 Cleared queue: {queue_name}")
    
    # Create a task using Celery
    test_filename = "email_01_marketing_shopify_com.json"
    print(f"📧 Creating task for: {test_filename}")
    
    # Queue the task
    result = process_email_task.delay(test_filename)
    print(f"✅ Task queued with ID: {result.id}")
    
    # Check what's in the queue
    queue_length = redis_client.llen(queue_name)
    print(f"📊 Queue length: {queue_length}")
    
    if queue_length > 0:
        # Peek at the message without removing it
        message = redis_client.lindex(queue_name, 0)
        if message:
            try:
                # Try to decode as JSON
                message_str = message.decode('utf-8')
                message_data = json.loads(message_str)
                
                print("\n📋 Celery Message Format:")
                print(json.dumps(message_data, indent=2))
                
                # Extract key information
                if 'body' in message_data:
                    print("\n📦 Message Body:")
                    body_data = json.loads(message_data['body'])
                    print(json.dumps(body_data, indent=2))
                
            except Exception as e:
                print(f"❌ Failed to decode message: {e}")
                print(f"Raw message: {message}")
    
    # Clean up
    redis_client.delete(queue_name)
    print(f"\n🧹 Cleaned up queue: {queue_name}")


def create_go_compatible_message(email_filename: str):
    """Create a message in the format that Go should use."""
    print(f"\n🔧 Creating Go-compatible message for: {email_filename}")

    task_id = str(uuid4())

    # Celery message body according to specification:
    # body = (args, kwargs, embed)
    message_body = [
        [email_filename],  # args
        {},               # kwargs
        {                 # embed
            "callbacks": None,
            "errbacks": None,
            "chain": None,
            "chord": None,
        }
    ]

    # Complete Celery message format according to specification
    celery_message = {
        "body": json.dumps(message_body),
        "headers": {
            "lang": "py",
            "task": "app.tasks.process_email_task",
            "id": task_id,
            "root_id": task_id,
            "parent_id": None,
            "group": None,
            "meth": None,
            "shadow": None,
            "eta": None,
            "expires": None,
            "retries": 0,
            "timelimit": [None, None],
            "argsrepr": f"('{email_filename}',)",
            "kwargsrepr": "{}",
            "origin": "gen1@go-email-queue",
        },
        "properties": {
            "correlation_id": task_id,
            "content_type": "application/json",
            "content_encoding": "utf-8",
            "reply_to": None,  # optional
            "delivery_tag": 1,  # required by Kombu transport
            "delivery_mode": 2,  # persistent delivery
            "priority": 0,      # default priority
            "delivery_info": {
                "exchange": "",
                "routing_key": "celery",
            },
        },
    }

    print("📋 Complete Celery Message Format (for Go):")
    print(json.dumps(celery_message, indent=2))
    
    # Test if this format works
    redis_client = redis.from_url(settings.redis_url)
    queue_name = "test_queue"

    # Push the celery message
    redis_client.lpush(queue_name, json.dumps(celery_message))
    print(f"✅ Pushed celery message to {queue_name}")

    # Check if we can retrieve it
    retrieved = redis_client.rpop(queue_name)
    if retrieved:
        retrieved_data = json.loads(retrieved.decode('utf-8'))
        print("✅ Successfully retrieved message:")
        print(json.dumps(retrieved_data, indent=2))
    
    # Clean up
    redis_client.delete(queue_name)


def main():
    """Main function."""
    try:
        test_celery_message_format()
        create_go_compatible_message("email_01_marketing_shopify_com.json")
        
        print("\n💡 Recommendations for Go service:")
        print("1. Use the simple message format shown above")
        print("2. Push directly to Redis queue without complex wrapping")
        print("3. Ensure task name matches exactly: 'app.tasks.process_email_task'")
        print("4. Use LPUSH to add messages to the queue")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error("Celery queue test failed", error=str(e))


if __name__ == "__main__":
    main()
