#!/usr/bin/env python3
"""
Test DynamoDB Decimal Conversion

This script tests the DynamoDB service to ensure float values are properly
converted to Decimal types for DynamoDB compatibility.
"""

import sys
import os
from decimal import Decimal

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from app.database.dynamodb import DynamoDBService

logger = structlog.get_logger()


def test_float_to_decimal_conversion():
    """Test the float to decimal conversion method."""
    print("🔍 Testing Float to Decimal Conversion")
    print("=" * 40)
    
    try:
        # Initialize DynamoDB service
        db_service = DynamoDBService()
        
        # Test data with various float values
        test_data = {
            'confidence_score': 0.85,
            'nested_data': {
                'score': 0.75,
                'probability': 0.9,
                'string_value': 'test',
                'int_value': 42
            },
            'list_with_floats': [0.1, 0.2, 0.3, 'string', 100],
            'string_field': 'no conversion needed',
            'int_field': 123
        }
        
        print(f"📋 Original data types:")
        print(f"  confidence_score: {type(test_data['confidence_score'])} = {test_data['confidence_score']}")
        print(f"  nested score: {type(test_data['nested_data']['score'])} = {test_data['nested_data']['score']}")
        print(f"  list floats: {[type(x) for x in test_data['list_with_floats']]}")
        
        # Convert using the service method
        converted_data = db_service._convert_floats_to_decimal(test_data)
        
        print(f"\n✅ Converted data types:")
        print(f"  confidence_score: {type(converted_data['confidence_score'])} = {converted_data['confidence_score']}")
        print(f"  nested score: {type(converted_data['nested_data']['score'])} = {converted_data['nested_data']['score']}")
        print(f"  list types: {[type(x) for x in converted_data['list_with_floats']]}")
        
        # Verify conversions
        assert isinstance(converted_data['confidence_score'], Decimal)
        assert isinstance(converted_data['nested_data']['score'], Decimal)
        assert isinstance(converted_data['nested_data']['probability'], Decimal)
        assert isinstance(converted_data['list_with_floats'][0], Decimal)
        assert isinstance(converted_data['list_with_floats'][1], Decimal)
        assert isinstance(converted_data['list_with_floats'][2], Decimal)
        
        # Verify non-float values are unchanged
        assert isinstance(converted_data['string_field'], str)
        assert isinstance(converted_data['int_field'], int)
        assert isinstance(converted_data['nested_data']['string_value'], str)
        assert isinstance(converted_data['nested_data']['int_value'], int)
        assert isinstance(converted_data['list_with_floats'][3], str)
        assert isinstance(converted_data['list_with_floats'][4], int)
        
        print(f"\n🎉 All conversion tests passed!")
        return True
        
    except Exception as exc:
        print(f"❌ Float to decimal conversion test failed: {exc}")
        logger.error("Decimal conversion test failed", error=str(exc))
        return False


def test_dynamodb_storage():
    """Test storing data with float values in DynamoDB."""
    print(f"\n💾 Testing DynamoDB Storage with Floats")
    print("-" * 40)
    
    try:
        from app.models import ProcessedEmail, EmailCategory, BusinessEntity, ExtractedData, EmailMetadata
        from datetime import datetime, timezone
        
        # Create test processed email with float confidence score
        processed_email = ProcessedEmail(
            email_category=EmailCategory.MARKETING,
            business_entity=BusinessEntity(
                name="Test Company",
                website=None,
                industry=None,
                location=None,
                dpo_email=None
            ),
            data=ExtractedData(
                email=[],
                phone_number=[],
                credit_card_number=[]
            ),
            confidence_score=0.85,  # This is a float that needs conversion
            processed_at=datetime.now(timezone.utc),
            metadata=EmailMetadata(
                sender_domain="test.com",
                footer_text=None,
                urls=[]
            )
        )
        
        print(f"📧 Test email confidence score: {processed_email.confidence_score} ({type(processed_email.confidence_score)})")
        
        # Initialize DynamoDB service
        db_service = DynamoDBService()
        
        # Store the result (this should convert floats to decimals internally)
        doc_id = db_service.store_result(processed_email)
        
        print(f"✅ Successfully stored email with doc_id: {doc_id}")
        
        # Retrieve the stored result to verify
        retrieved_result = db_service.get_result(doc_id)
        
        if retrieved_result:
            print(f"✅ Successfully retrieved stored result")
            print(f"  Stored confidence score: {retrieved_result.get('confidence_score')} ({type(retrieved_result.get('confidence_score'))})")
            
            # Clean up - delete the test record
            db_service.table.delete_item(Key={'id': doc_id})
            print(f"🧹 Cleaned up test record")
        else:
            print(f"❌ Failed to retrieve stored result")
            return False
        
        return True
        
    except Exception as exc:
        print(f"❌ DynamoDB storage test failed: {exc}")
        logger.error("DynamoDB storage test failed", error=str(exc))
        return False


def main():
    """Main function."""
    print("🧪 DynamoDB Decimal Conversion Testing")
    print("=" * 50)
    
    tests = [
        ("Float to Decimal Conversion", test_float_to_decimal_conversion),
        ("DynamoDB Storage", test_dynamodb_storage),
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
        print("✅ All DynamoDB decimal tests passed!")
        print("\n💡 DynamoDB should now handle float values correctly.")
    else:
        print("❌ Some tests failed. Check the configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
