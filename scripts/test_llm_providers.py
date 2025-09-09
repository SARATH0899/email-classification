#!/usr/bin/env python3
"""
LLM Provider Testing Script

This script tests different LLM providers (OpenAI, Gemini, Ollama) for email classification.
It demonstrates the flexibility of the modular LLM system.
"""

import sys
import os
import json
import time
from typing import Dict, Any, List
import structlog

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import EmailInput, EmailMetadata
from app.llm.chains import EmailClassificationChain
from app.llm.models import model_manager

logger = structlog.get_logger()


class LLMProviderTester:
    """Test different LLM providers for email classification."""
    
    def __init__(self):
        """Initialize the LLM provider tester."""
        self.test_email = self._create_test_email()
        self.results = {}
    
    def _create_test_email(self) -> tuple:
        """Create a test email for classification."""
        email_content = """
        🚀 Black Friday Sale - 50% Off Everything!
        
        Dear John Doe,
        
        Don't miss our biggest sale of the year! Get 50% off on all products.
        Your email: john.doe@example.com
        Phone: +1-555-123-4567
        
        Shop now at https://shopify.com/sale
        
        Best regards,
        The Shopify Team
        
        ---
        Shopify Inc.
        150 Elgin Street, Ottawa, ON
        Unsubscribe: https://shopify.com/unsubscribe
        """
        
        metadata = EmailMetadata(
            sender_domain="shopify.com",
            footer_text="Shopify Inc.\n150 Elgin Street, Ottawa, ON\nUnsubscribe: https://shopify.com/unsubscribe",
            urls=["https://shopify.com/sale", "https://shopify.com/unsubscribe"]
        )
        
        return email_content.strip(), metadata
    
    def test_provider(self, provider_name: str, api_key: str = None) -> Dict[str, Any]:
        """
        Test a specific LLM provider.
        
        Args:
            provider_name: Name of the provider (openai, gemini, ollama)
            api_key: API key for the provider (if required)
            
        Returns:
            Test results dictionary
        """
        print(f"\n🧪 Testing {provider_name.upper()} Provider")
        print("-" * 40)
        
        # Set environment variables for the provider
        original_provider = os.environ.get('LLM_PROVIDER')
        os.environ['LLM_PROVIDER'] = provider_name
        
        if api_key:
            if provider_name == 'openai':
                os.environ['OPENAI_API_KEY'] = api_key
            elif provider_name == 'gemini':
                os.environ['GEMINI_API_KEY'] = api_key
        
        try:
            # Reload settings to pick up new environment variables
            from importlib import reload
            from app import config
            reload(config)
            
            # Create classification chain
            chain = EmailClassificationChain()
            
            # Test classification
            email_content, metadata = self.test_email
            
            start_time = time.time()
            result = chain.classify_email(email_content, metadata)
            processing_time = time.time() - start_time
            
            # Collect results
            test_result = {
                'provider': provider_name,
                'success': True,
                'processing_time': processing_time,
                'category': result.email_category.value,
                'business_name': result.business_entity.name,
                'confidence': result.confidence_score,
                'extracted_emails': len(result.data.email or []),
                'extracted_phones': len(result.data.phone_number or []),
                'model_info': chain.model_name
            }
            
            print(f"✅ Success!")
            print(f"   Category: {result.email_category.value}")
            print(f"   Business: {result.business_entity.name}")
            print(f"   Confidence: {result.confidence_score:.3f}")
            print(f"   Processing Time: {processing_time:.2f}s")
            print(f"   Extracted Data: {len(result.data.email or [])} emails, {len(result.data.phone_number or [])} phones")
            
            return test_result
            
        except Exception as exc:
            print(f"❌ Failed: {exc}")
            return {
                'provider': provider_name,
                'success': False,
                'error': str(exc),
                'processing_time': None
            }
        
        finally:
            # Restore original environment
            if original_provider:
                os.environ['LLM_PROVIDER'] = original_provider
            elif 'LLM_PROVIDER' in os.environ:
                del os.environ['LLM_PROVIDER']
    
    def test_all_providers(self) -> Dict[str, Any]:
        """Test all available LLM providers."""
        print("🚀 Testing All LLM Providers")
        print("=" * 50)
        
        providers_to_test = [
            {
                'name': 'openai',
                'api_key': os.environ.get('OPENAI_API_KEY'),
                'required': True
            },
            {
                'name': 'gemini',
                'api_key': os.environ.get('GEMINI_API_KEY'),
                'required': False
            },
            {
                'name': 'ollama',
                'api_key': None,
                'required': False
            }
        ]
        
        results = {}
        
        for provider_config in providers_to_test:
            provider_name = provider_config['name']
            api_key = provider_config['api_key']
            required = provider_config['required']
            
            if required and not api_key and provider_name != 'ollama':
                print(f"\n⚠️  Skipping {provider_name.upper()} - API key not provided")
                results[provider_name] = {
                    'provider': provider_name,
                    'success': False,
                    'error': 'API key not provided',
                    'skipped': True
                }
                continue
            
            result = self.test_provider(provider_name, api_key)
            results[provider_name] = result
        
        return results
    
    def compare_providers(self, results: Dict[str, Any]):
        """Compare results from different providers."""
        print("\n📊 Provider Comparison")
        print("=" * 50)
        
        successful_results = {k: v for k, v in results.items() if v.get('success', False)}
        
        if not successful_results:
            print("❌ No successful provider tests to compare")
            return
        
        print(f"✅ Successful Providers: {len(successful_results)}/{len(results)}")
        print()
        
        # Compare processing times
        print("⏱️  Processing Times:")
        for provider, result in successful_results.items():
            time_str = f"{result['processing_time']:.2f}s" if result['processing_time'] else "N/A"
            print(f"   {provider.upper()}: {time_str}")
        
        # Compare classifications
        print("\n🏷️  Classifications:")
        categories = {}
        for provider, result in successful_results.items():
            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(provider)
        
        for category, providers in categories.items():
            providers_str = ", ".join(p.upper() for p in providers)
            print(f"   {category}: {providers_str}")
        
        # Compare confidence scores
        print("\n📈 Confidence Scores:")
        for provider, result in successful_results.items():
            confidence = result.get('confidence', 0)
            print(f"   {provider.upper()}: {confidence:.3f}")
        
        # Find best performer
        if len(successful_results) > 1:
            # Sort by confidence score (descending) and processing time (ascending)
            sorted_results = sorted(
                successful_results.items(),
                key=lambda x: (-x[1].get('confidence', 0), x[1].get('processing_time', float('inf')))
            )
            
            best_provider = sorted_results[0][0]
            print(f"\n🏆 Best Performer: {best_provider.upper()}")
    
    def run_comprehensive_test(self):
        """Run comprehensive LLM provider testing."""
        print("🧪 LLM Provider Comprehensive Testing")
        print("=" * 60)
        
        # Test all providers
        results = self.test_all_providers()
        
        # Compare results
        self.compare_providers(results)
        
        # Save results to file
        results_file = "test_data/llm_provider_results.json"
        os.makedirs("test_data", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Print summary
        successful_count = sum(1 for r in results.values() if r.get('success', False))
        print(f"\n📋 Summary:")
        print(f"   Total Providers Tested: {len(results)}")
        print(f"   Successful: {successful_count}")
        print(f"   Failed: {len(results) - successful_count}")
        
        return results


def main():
    """Main function to run LLM provider testing."""
    tester = LLMProviderTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        # Print usage instructions
        print("\n💡 Usage Instructions:")
        print("   Set LLM_PROVIDER environment variable to choose provider:")
        print("   - export LLM_PROVIDER=openai")
        print("   - export LLM_PROVIDER=gemini") 
        print("   - export LLM_PROVIDER=ollama")
        print("\n   Make sure to set appropriate API keys:")
        print("   - OPENAI_API_KEY for OpenAI")
        print("   - GEMINI_API_KEY for Gemini")
        print("   - OLLAMA_BASE_URL for Ollama (default: http://localhost:11434)")
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as exc:
        print(f"\n❌ Testing failed: {exc}")
        logger.error("LLM provider testing failed", error=str(exc))


if __name__ == "__main__":
    main()
