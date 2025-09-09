"""Tests for the main email processor."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email_processor import EmailProcessor
from app.models import EmailInput, EmailCategory, ProcessedEmail


class TestEmailProcessor:
    """Test cases for EmailProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create email processor with mocked services."""
        with patch.multiple(
            'app.services.email_processor',
            HTMLProcessor=Mock,
            PIIProcessor=Mock,
            MetadataExtractor=Mock,
            VectorStoreService=Mock,
            SimilarityMatcher=Mock,
            EmailClassificationChain=Mock,
            PrivacyPolicyScraperTool=Mock
        ):
            return EmailProcessor()
    
    def test_process_email_with_confident_match(self, processor, sample_email_input, sample_metadata):
        """Test email processing with confident vector match."""
        # Setup mocks
        processor.html_processor.strip_html.return_value = "Clean text content"
        processor.pii_processor.anonymize_text.return_value = "Anonymized text"
        processor.metadata_extractor.extract_metadata.return_value = sample_metadata
        
        # Mock confident vector match
        mock_vector_match = Mock()
        mock_vector_match.confidence_score = 0.9
        processor.similarity_matcher.find_best_match.return_value = mock_vector_match
        processor.similarity_matcher.is_confident_match.return_value = True
        
        # Mock business entity extraction
        from app.models import BusinessEntity
        mock_business_entity = BusinessEntity(name="Test Company")
        processor.similarity_matcher.extract_business_entity_from_match.return_value = mock_business_entity
        processor.similarity_matcher.get_email_category_from_match.return_value = EmailCategory.MARKETING
        
        # Mock PII data extraction
        processor.pii_processor.extract_pii_data.return_value = {
            'email': ['user@example.com'],
            'phone_number': [],
            'credit_card_number': []
        }
        
        # Process email
        result = processor.process_email(sample_email_input)
        
        # Assertions
        assert isinstance(result, ProcessedEmail)
        assert result.email_category == EmailCategory.MARKETING
        assert result.business_entity.name == "Test Company"
        assert result.confidence_score == 0.9
        assert result.data.email == ['user@example.com']
        assert result.processed_at is not None
    
    def test_process_email_with_llm_fallback(self, processor, sample_email_input, sample_metadata):
        """Test email processing with LLM fallback."""
        # Setup mocks
        processor.html_processor.strip_html.return_value = "Clean text content"
        processor.pii_processor.anonymize_text.return_value = "Anonymized text"
        processor.metadata_extractor.extract_metadata.return_value = sample_metadata
        
        # Mock no confident vector match
        processor.similarity_matcher.find_best_match.return_value = None
        
        # Mock LLM classification
        from app.models import BusinessEntity, ExtractedData
        mock_processed_email = ProcessedEmail(
            email_category=EmailCategory.MARKETING,
            business_entity=BusinessEntity(name="LLM Company"),
            data=ExtractedData(),
            confidence_score=0.7,
            metadata=sample_metadata
        )
        processor.llm_classifier.classify_email.return_value = mock_processed_email
        
        # Mock PII data extraction
        processor.pii_processor.extract_pii_data.return_value = {
            'email': [],
            'phone_number': ['123-456-7890'],
            'credit_card_number': []
        }
        
        # Process email
        result = processor.process_email(sample_email_input)
        
        # Assertions
        assert isinstance(result, ProcessedEmail)
        assert result.email_category == EmailCategory.MARKETING
        assert result.business_entity.name == "LLM Company"
        assert result.confidence_score == 0.7
        assert result.data.phone_number == ['123-456-7890']
    
    def test_html_stripping(self, processor, sample_email_input):
        """Test HTML content stripping."""
        processor.html_processor.strip_html.return_value = "Stripped content"
        
        result = processor._strip_html_content(sample_email_input)
        
        assert result == "Stripped content"
        processor.html_processor.strip_html.assert_called_once_with(sample_email_input.html_content)
    
    def test_html_stripping_fallback_to_text(self, processor):
        """Test HTML stripping fallback to text content."""
        email_input = EmailInput(
            from_email="test@example.com",
            subject="Test",
            html_content=None,
            text_content="Plain text content"
        )
        
        result = processor._strip_html_content(email_input)
        
        assert result == "Plain text content"
    
    def test_pii_anonymization(self, processor):
        """Test PII anonymization."""
        processor.pii_processor.anonymize_text.return_value = "Anonymized content"
        
        result = processor._anonymize_pii("Original content")
        
        assert result == "Anonymized content"
        processor.pii_processor.anonymize_text.assert_called_once_with("Original content")
    
    def test_pii_anonymization_fallback(self, processor):
        """Test PII anonymization fallback on error."""
        processor.pii_processor.anonymize_text.side_effect = Exception("PII error")
        
        result = processor._anonymize_pii("Original content")
        
        assert result == "Original content"  # Should return original on error
    
    def test_metadata_extraction(self, processor, sample_email_input, sample_metadata):
        """Test metadata extraction."""
        processor.metadata_extractor.extract_metadata.return_value = sample_metadata
        
        result = processor._extract_metadata(sample_email_input, "clean text")
        
        assert result == sample_metadata
        processor.metadata_extractor.extract_metadata.assert_called_once_with(
            sample_email_input, "clean text"
        )
    
    def test_vector_matching(self, processor, sample_metadata):
        """Test vector similarity matching."""
        mock_match = Mock()
        mock_match.confidence_score = 0.85
        processor.similarity_matcher.find_best_match.return_value = mock_match
        
        result = processor._find_vector_match("text", sample_metadata)
        
        assert result == mock_match
        processor.similarity_matcher.find_best_match.assert_called_once_with("text", sample_metadata)
    
    def test_user_data_extraction(self, processor):
        """Test user data extraction."""
        processor.pii_processor.extract_pii_data.return_value = {
            'email': ['user@test.com'],
            'phone_number': ['555-1234'],
            'credit_card_number': ['4111-1111-1111-1111']
        }
        
        result = processor._extract_user_data("test content")
        
        assert result.email == ['user@test.com']
        assert result.phone_number == ['555-1234']
        assert result.credit_card_number == ['4111-1111-1111-1111']
    
    def test_business_entity_enhancement_with_dpo_scraping(self, processor):
        """Test business entity enhancement with DPO scraping."""
        from app.models import BusinessEntity
        
        # Create processed email with business entity missing DPO email
        business_entity = BusinessEntity(
            name="Test Company",
            website="https://example.com",
            dpo_email=None
        )
        
        processed_email = ProcessedEmail(
            email_category=EmailCategory.MARKETING,
            business_entity=business_entity,
            data=Mock(),
            confidence_score=0.8
        )
        
        # Mock privacy scraper result
        processor.privacy_scraper._run.return_value = '{"success": true, "dpo_email": "dpo@example.com"}'
        
        result = processor._enhance_business_entity(processed_email)
        
        assert result.business_entity.dpo_email == "dpo@example.com"
        processor.privacy_scraper._run.assert_called_once_with("https://example.com")
    
    def test_vector_db_storage(self, processor, sample_metadata):
        """Test storing processed email in vector database."""
        from app.models import BusinessEntity
        
        processed_email = ProcessedEmail(
            email_category=EmailCategory.MARKETING,
            business_entity=BusinessEntity(name="Test Company"),
            data=Mock(),
            confidence_score=0.9,
            metadata=sample_metadata
        )
        
        processor.vector_store.add_email_embedding.return_value = "doc-123"
        
        processor._store_in_vector_db("text content", processed_email)
        
        processor.vector_store.add_email_embedding.assert_called_once_with(
            email_content="text content",
            metadata=sample_metadata,
            email_category=EmailCategory.MARKETING,
            business_entity=processed_email.business_entity,
            confidence_score=0.9
        )
