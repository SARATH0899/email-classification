#!/usr/bin/env python3
"""
Test Privacy Policy Scraper

This script tests the privacy policy scraper to ensure it initializes correctly
and doesn't have the "dpo_chain" field error.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from app.services.privacy_policy_scraper import PrivacyPolicyScraperTool

logger = structlog.get_logger()


def test_privacy_scraper_initialization():
    """Test privacy policy scraper initialization."""
    print("🔍 Testing Privacy Policy Scraper Initialization")
    print("=" * 50)
    
    try:
        # Test initialization
        print("📋 Initializing PrivacyPolicyScraperTool...")
        scraper = PrivacyPolicyScraperTool()
        print("✅ PrivacyPolicyScraperTool initialized successfully")
        
        # Test basic properties
        print(f"\n📊 Tool Properties:")
        print(f"  Name: {scraper.name}")
        print(f"  Description: {scraper.description}")
        print(f"  Has DPO Chain: {hasattr(scraper, 'dpo_chain')}")
        
        if hasattr(scraper, 'dpo_chain'):
            print(f"  DPO Chain Type: {type(scraper.dpo_chain).__name__}")
        
        # Test tool schema
        print(f"\n📋 Tool Schema:")
        print(f"  Args Schema: {scraper.args_schema.__name__}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Privacy scraper initialization failed: {exc}")
        logger.error("Privacy scraper test failed", error=str(exc))
        return False


def test_dpo_chain():
    """Test DPO extraction chain separately."""
    print(f"\n🔗 Testing DPO Extraction Chain")
    print("-" * 30)
    
    try:
        from app.llm.chains import DPOExtractionChain
        
        print("📋 Initializing DPOExtractionChain...")
        dpo_chain = DPOExtractionChain()
        print("✅ DPOExtractionChain initialized successfully")
        
        # Test basic properties
        print(f"  Chain Type: {type(dpo_chain).__name__}")
        
        return True
        
    except Exception as exc:
        print(f"❌ DPO chain test failed: {exc}")
        return False


def test_tool_input_schema():
    """Test the tool input schema."""
    print(f"\n📝 Testing Tool Input Schema")
    print("-" * 30)
    
    try:
        from app.services.privacy_policy_scraper import PrivacyPolicyScraperInput
        
        # Test creating input
        test_input = PrivacyPolicyScraperInput(
            website_url="https://example.com",
            company_name="Example Corp"
        )
        
        print("✅ PrivacyPolicyScraperInput created successfully")
        print(f"  Website URL: {test_input.website_url}")
        print(f"  Company Name: {test_input.company_name}")
        
        return True
        
    except Exception as exc:
        print(f"❌ Tool input schema test failed: {exc}")
        return False


def main():
    """Main function."""
    print("🧪 Privacy Policy Scraper Testing")
    print("=" * 50)
    
    tests = [
        ("DPO Chain", test_dpo_chain),
        ("Tool Input Schema", test_tool_input_schema),
        ("Privacy Scraper Initialization", test_privacy_scraper_initialization),
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
        print("✅ All privacy scraper tests passed!")
        print("\n💡 The privacy policy scraper should now work without field errors.")
    else:
        print("❌ Some tests failed. Check the configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
