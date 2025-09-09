#!/usr/bin/env python3
"""
Startup Script

This script handles different startup modes for the application.
"""

import sys
import os
import argparse

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all imports."""
    from scripts.test_imports import test_imports
    return test_imports()

def generate_emails():
    """Generate test emails."""
    from scripts.generate_test_emails import main
    main()

def run_processing():
    """Run email processing."""
    from scripts.run_email_processing import main
    main()

def test_providers():
    """Test LLM providers."""
    from scripts.test_llm_providers import main
    main()

def health_check():
    """Run health check."""
    from scripts.health_check import main
    main()

def test_queue():
    """Test Celery queue format."""
    from scripts.test_celery_queue import main
    main()

def debug_queue():
    """Debug Celery queue format."""
    from scripts.debug_celery_format import main
    main()

def test_pii():
    """Test PII configuration."""
    from scripts.test_pii_config import main
    main()

def test_privacy():
    """Test privacy policy scraper."""
    from scripts.test_privacy_scraper import main
    main()

def test_dynamodb():
    """Test DynamoDB decimal conversion."""
    from scripts.test_dynamodb_decimal import main
    main()

def test_error_fixes():
    """Test all error fixes."""
    from scripts.test_error_fixes import main
    main()

def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description='Email Processing Application Startup')
    parser.add_argument('command', choices=['test-imports', 'generate-emails', 'run-processing', 'test-providers', 'health-check', 'test-queue', 'debug-queue', 'test-pii', 'test-privacy', 'test-dynamodb', 'test-error-fixes'],
                       help='Command to run')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting: {args.command}")
    
    try:
        if args.command == 'test-imports':
            success = test_imports()
            sys.exit(0 if success else 1)
        elif args.command == 'generate-emails':
            generate_emails()
        elif args.command == 'run-processing':
            run_processing()
        elif args.command == 'test-providers':
            test_providers()
        elif args.command == 'health-check':
            health_check()
        elif args.command == 'test-queue':
            test_queue()
        elif args.command == 'debug-queue':
            debug_queue()
        elif args.command == 'test-pii':
            test_pii()
        elif args.command == 'test-privacy':
            test_privacy()
        elif args.command == 'test-dynamodb':
            test_dynamodb()
        elif args.command == 'test-error-fixes':
            test_error_fixes()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
