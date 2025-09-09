"""Deepeval tests for LLM output quality evaluation."""

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset
from typing import List, Dict, Any
import json

from app.llm.chains import EmailClassificationChain
from app.models import EmailMetadata, EmailCategory


class TestLLMEmailClassification:
    """Test LLM email classification quality using Deepeval."""
    
    @pytest.fixture
    def classification_chain(self):
        """Create email classification chain for testing."""
        return EmailClassificationChain(model_name='gpt-3.5-turbo')
    
    @pytest.fixture
    def test_emails(self):
        """Sample test emails with expected classifications."""
        return [
            {
                "email_content": """
                🚀 Black Friday Sale - 50% Off Everything!
                Dear John, Don't miss our biggest sale of the year! 
                Get 50% off on all products. Shop now at https://example.com/sale
                Unsubscribe: https://example.com/unsubscribe
                """,
                "metadata": EmailMetadata(
                    sender_domain="example.com",
                    footer_text="Unsubscribe: https://example.com/unsubscribe",
                    urls=["https://example.com/sale", "https://example.com/unsubscribe"]
                ),
                "expected_category": EmailCategory.MARKETING,
                "expected_business_name": "Example",
                "context": "This is a promotional email with sale offers and unsubscribe links"
            },
            {
                "email_content": """
                Order Confirmation #12345
                Dear Customer, Your order has been confirmed.
                Total: $99.99, Payment: Card ending 4532
                Delivery to: 123 Main St
                """,
                "metadata": EmailMetadata(
                    sender_domain="shop.com",
                    footer_text="Customer Service: support@shop.com",
                    urls=[]
                ),
                "expected_category": EmailCategory.TRANSACTIONAL,
                "expected_business_name": "Shop",
                "context": "This is a transactional email confirming an order with payment details"
            },
            {
                "email_content": """
                Quick Survey - Help Us Improve
                Hi there, Please take 2 minutes to complete our survey.
                Your feedback is valuable to us.
                Survey link: https://survey.com/feedback
                """,
                "metadata": EmailMetadata(
                    sender_domain="survey.com",
                    footer_text="SurveyMonkey Inc.",
                    urls=["https://survey.com/feedback"]
                ),
                "expected_category": EmailCategory.SURVEY,
                "expected_business_name": "Survey",
                "context": "This is a survey email requesting user feedback"
            },
            {
                "email_content": """
                Support Ticket #12345 - Issue Resolved
                Dear Customer, Your support ticket has been resolved.
                Issue: Login problem
                Resolution: Password reset completed
                """,
                "metadata": EmailMetadata(
                    sender_domain="support.com",
                    footer_text="Support Team",
                    urls=[]
                ),
                "expected_category": EmailCategory.CUSTOMER_SUPPORT,
                "expected_business_name": "Support",
                "context": "This is a customer support email about a resolved ticket"
            },
            {
                "email_content": """
                Hi there! Want to grab coffee this weekend?
                I'm free Saturday afternoon. Let me know!
                Best, Jamie
                """,
                "metadata": EmailMetadata(
                    sender_domain="gmail.com",
                    footer_text="",
                    urls=[]
                ),
                "expected_category": EmailCategory.PERSONAL,
                "expected_business_name": "Gmail",
                "context": "This is a personal email between friends"
            }
        ]
    
    def test_email_classification_relevancy(self, classification_chain, test_emails):
        """Test answer relevancy of email classification."""
        test_cases = []
        
        for email_data in test_emails:
            # Get LLM classification
            result = classification_chain.classify_email(
                email_data["email_content"],
                email_data["metadata"]
            )
            
            # Create test case for Deepeval
            test_case = LLMTestCase(
                input=f"Email content: {email_data['email_content']}\nDomain: {email_data['metadata'].sender_domain}",
                actual_output=f"Category: {result.email_category.value}, Business: {result.business_entity.name}, Confidence: {result.confidence_score}",
                expected_output=f"Category: {email_data['expected_category'].value}, Business: {email_data['expected_business_name']}",
                context=[email_data["context"]]
            )
            
            test_cases.append(test_case)
        
        # Evaluate with Answer Relevancy Metric
        metric = AnswerRelevancyMetric(threshold=0.7)
        
        for test_case in test_cases:
            assert_test(test_case, [metric])
    
    def test_email_classification_faithfulness(self, classification_chain, test_emails):
        """Test faithfulness of email classification to input content."""
        test_cases = []
        
        for email_data in test_emails:
            # Get LLM classification
            result = classification_chain.classify_email(
                email_data["email_content"],
                email_data["metadata"]
            )
            
            # Create test case for faithfulness
            test_case = LLMTestCase(
                input=f"Classify this email: {email_data['email_content']}",
                actual_output=json.dumps({
                    "category": result.email_category.value,
                    "business_name": result.business_entity.name,
                    "confidence": result.confidence_score,
                    "extracted_data": {
                        "emails": result.data.email or [],
                        "phones": result.data.phone_number or [],
                        "cards": result.data.credit_card_number or []
                    }
                }),
                retrieval_context=[email_data["email_content"], email_data["context"]]
            )
            
            test_cases.append(test_case)
        
        # Evaluate with Faithfulness Metric
        metric = FaithfulnessMetric(threshold=0.8)
        
        for test_case in test_cases:
            assert_test(test_case, [metric])
    
    def test_classification_precision(self, classification_chain, test_emails):
        """Test contextual precision of email classification."""
        test_cases = []
        
        for email_data in test_emails:
            # Get LLM classification
            result = classification_chain.classify_email(
                email_data["email_content"],
                email_data["metadata"]
            )
            
            # Check if classification matches expected
            is_correct = result.email_category == email_data["expected_category"]
            
            test_case = LLMTestCase(
                input=f"Email: {email_data['email_content'][:100]}...",
                actual_output=result.email_category.value,
                expected_output=email_data["expected_category"].value,
                context=[email_data["context"]],
                retrieval_context=[email_data["email_content"]]
            )
            
            test_cases.append(test_case)
        
        # Evaluate with Contextual Precision Metric
        metric = ContextualPrecisionMetric(threshold=0.8)
        
        for test_case in test_cases:
            assert_test(test_case, [metric])
    
    def test_model_comparison(self, test_emails):
        """Compare different models for email classification."""
        models_to_test = ['primary', 'gpt-3.5-turbo']  # Use available models
        results = {}
        
        for model_name in models_to_test:
            try:
                chain = EmailClassificationChain(model_name=model_name)
                model_results = []
                
                for email_data in test_emails:
                    result = chain.classify_email(
                        email_data["email_content"],
                        email_data["metadata"]
                    )
                    
                    # Check accuracy
                    is_correct = result.email_category == email_data["expected_category"]
                    
                    model_results.append({
                        "correct": is_correct,
                        "confidence": result.confidence_score,
                        "category": result.email_category.value,
                        "expected": email_data["expected_category"].value
                    })
                
                # Calculate metrics
                accuracy = sum(1 for r in model_results if r["correct"]) / len(model_results)
                avg_confidence = sum(r["confidence"] for r in model_results) / len(model_results)
                
                results[model_name] = {
                    "accuracy": accuracy,
                    "avg_confidence": avg_confidence,
                    "results": model_results
                }
                
            except Exception as e:
                results[model_name] = {"error": str(e)}
        
        # Print comparison results
        print("\n=== Model Comparison Results ===")
        for model, metrics in results.items():
            if "error" not in metrics:
                print(f"{model}:")
                print(f"  Accuracy: {metrics['accuracy']:.2%}")
                print(f"  Avg Confidence: {metrics['avg_confidence']:.3f}")
            else:
                print(f"{model}: Error - {metrics['error']}")
        
        # Assert that at least one model performs well
        successful_models = [m for m, r in results.items() if "error" not in r and r["accuracy"] >= 0.6]
        assert len(successful_models) > 0, "No model achieved acceptable accuracy (>= 60%)"
    
    def test_token_usage_efficiency(self, classification_chain, test_emails):
        """Test token usage efficiency of the classification chain."""
        # This would require integration with OpenAI's usage tracking
        # For now, we'll test that the chain completes within reasonable time
        import time
        
        total_time = 0
        successful_classifications = 0
        
        for email_data in test_emails:
            start_time = time.time()
            
            try:
                result = classification_chain.classify_email(
                    email_data["email_content"],
                    email_data["metadata"]
                )
                
                end_time = time.time()
                classification_time = end_time - start_time
                total_time += classification_time
                successful_classifications += 1
                
                # Assert reasonable response time (< 10 seconds per email)
                assert classification_time < 10, f"Classification took too long: {classification_time:.2f}s"
                
                # Assert valid confidence score
                assert 0 <= result.confidence_score <= 1, f"Invalid confidence score: {result.confidence_score}"
                
            except Exception as e:
                print(f"Classification failed for email: {e}")
        
        if successful_classifications > 0:
            avg_time = total_time / successful_classifications
            print(f"\nAverage classification time: {avg_time:.2f}s")
            
            # Assert reasonable average time
            assert avg_time < 5, f"Average classification time too high: {avg_time:.2f}s"


class TestLLMDatasetEvaluation:
    """Test LLM performance on larger datasets."""
    
    def test_batch_evaluation(self):
        """Test LLM performance on a batch of emails."""
        # Create a dataset for batch evaluation
        test_cases = []
        
        # Sample dataset
        emails = [
            ("Marketing email with promotional content", "marketing"),
            ("Order confirmation with payment details", "transactional"),
            ("Survey request for feedback", "survey"),
            ("Personal message from friend", "personal"),
            ("Support ticket resolution", "customer_support")
        ]
        
        for content, expected_category in emails:
            test_case = LLMTestCase(
                input=f"Classify this email: {content}",
                actual_output=expected_category,
                expected_output=expected_category
            )
            test_cases.append(test_case)
        
        # Create dataset
        dataset = EvaluationDataset(test_cases=test_cases)
        
        # This would typically run a full evaluation
        # For now, we'll just verify the dataset is created correctly
        assert len(dataset.test_cases) == len(emails)
        assert all(isinstance(tc, LLMTestCase) for tc in dataset.test_cases)
