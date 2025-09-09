"""Main email processing service that orchestrates all components."""

from datetime import datetime, timezone
import structlog

from app.models import EmailInput, ProcessedEmail, EmailMetadata, ExtractedData
from app.config import settings
from app.processing.html_processor import HTMLProcessor
from app.processing.pii_processor import PIIProcessor
from app.services.metadata_extractor import MetadataExtractor
from app.database.vector_store import VectorStoreService
from app.services.similarity_matcher import SimilarityMatcher
from app.llm.chains import EmailClassificationChain
from app.services.privacy_policy_scraper import PrivacyPolicyScraperTool

logger = structlog.get_logger()


class EmailProcessor:
    """Main service for processing emails through the complete pipeline."""
    
    def __init__(self):
        """Initialize the email processor with all required services."""
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all processing services."""
        try:
            self.html_processor = HTMLProcessor()
            self.pii_processor = PIIProcessor()
            self.metadata_extractor = MetadataExtractor()
            self.vector_store = VectorStoreService()
            self.similarity_matcher = SimilarityMatcher()
            self.llm_classifier = EmailClassificationChain()
            self.privacy_scraper = PrivacyPolicyScraperTool()
            
            logger.info("Email processor services initialized successfully")
            
        except Exception as exc:
            logger.error("Failed to initialize email processor services", error=str(exc))
            raise
    
    def process_email(self, email_input: EmailInput) -> ProcessedEmail:
        """
        Process email through the complete pipeline.
        
        Args:
            email_input: Input email data
            
        Returns:
            ProcessedEmail with classification and extraction results
        """
        try:
            logger.info("Starting email processing pipeline", 
                       sender=email_input.from_email,
                       subject=email_input.subject[:50])
            
            # Step 1: HTML Stripping
            clean_text = self._strip_html_content(email_input)
            
            # Step 2: PII Anonymization
            anonymized_text = self._anonymize_pii(clean_text)
            
            # Step 3: Metadata Extraction
            metadata = self._extract_metadata(email_input, clean_text)
            
            # Step 4: Vector Similarity Search
            vector_match = self._find_vector_match(anonymized_text, metadata)
            
            # Step 5: Process based on confidence
            if vector_match and self.similarity_matcher.is_confident_match(vector_match):
                # High confidence match - use vector result
                processed_email = self._process_confident_match(
                    email_input, anonymized_text, metadata, vector_match
                )
            else:
                # Low confidence - use LLM classification
                processed_email = self._process_llm_classification(
                    anonymized_text, metadata
                )
            
            # Step 6: Enhance business entity if needed
            processed_email = self._enhance_business_entity(processed_email)
            
            # Step 7: Store in vector database if confident
            if processed_email.confidence_score > settings.confidence_threshold:
                self._store_in_vector_db(anonymized_text, processed_email)
            
            # Add processing timestamp
            processed_email.processed_at = datetime.now(timezone.utc).isoformat()
            
            logger.info("Email processing completed successfully",
                       category=processed_email.email_category.value,
                       confidence=processed_email.confidence_score,
                       business=processed_email.business_entity.name)
            
            return processed_email
            
        except Exception as exc:
            logger.error("Email processing failed", error=str(exc), exc_info=True)
            raise
    
    def _strip_html_content(self, email_input: EmailInput) -> str:
        """Strip HTML and get clean text content."""
        try:
            if email_input.html_content:
                clean_text = self.html_processor.strip_html(email_input.html_content)
            else:
                clean_text = email_input.text_content or ""
            
            # Truncate if too long
            if len(clean_text) > settings.max_email_length:
                clean_text = clean_text[:settings.max_email_length] + "..."
            
            logger.debug("HTML content stripped", length=len(clean_text))
            return clean_text
            
        except Exception as exc:
            logger.error("HTML stripping failed", error=str(exc))
            return email_input.text_content or ""
    
    def _anonymize_pii(self, text: str) -> str:
        """Anonymize PII in text content."""
        try:
            anonymized_text = self.pii_processor.anonymize_text(text)
            logger.debug("PII anonymization completed")
            return anonymized_text
            
        except Exception as exc:
            logger.error("PII anonymization failed", error=str(exc))
            return text  # Return original text if anonymization fails
    
    def _extract_metadata(self, email_input: EmailInput, clean_text: str) -> EmailMetadata:
        """Extract metadata from email."""
        try:
            metadata = self.metadata_extractor.extract_metadata(email_input, clean_text)
            logger.debug("Metadata extraction completed", 
                        domain=metadata.sender_domain,
                        urls_count=len(metadata.urls))
            return metadata
            
        except Exception as exc:
            logger.error("Metadata extraction failed", error=str(exc))
            # Return minimal metadata
            return EmailMetadata(
                sender_domain=self.metadata_extractor.extract_sender_domain(email_input.from_email),
                urls=[]
            )
    
    def _find_vector_match(self, text: str, metadata: EmailMetadata):
        """Find best vector similarity match."""
        try:
            vector_match = self.similarity_matcher.find_best_match(text, metadata)
            
            if vector_match:
                logger.debug("Vector match found", 
                           confidence=vector_match.confidence_score,
                           similarity=vector_match.similarity_score)
            else:
                logger.debug("No confident vector match found")
            
            return vector_match
            
        except Exception as exc:
            logger.error("Vector matching failed", error=str(exc))
            return None
    
    def _process_confident_match(self, email_input, text, metadata, vector_match) -> ProcessedEmail:
        """Process email using confident vector match."""
        try:
            # Extract business entity from match
            business_entity = self.similarity_matcher.extract_business_entity_from_match(vector_match)
            
            # Extract email category from match
            email_category = self.similarity_matcher.get_email_category_from_match(vector_match)
            
            # Extract user data from original text
            extracted_data = self._extract_user_data(text)
            
            processed_email = ProcessedEmail(
                email_category=email_category,
                business_entity=business_entity,
                data=extracted_data,
                confidence_score=vector_match.confidence_score,
                metadata=metadata
            )
            
            logger.info("Processed using confident vector match",
                       category=email_category.value,
                       confidence=vector_match.confidence_score)
            
            return processed_email
            
        except Exception as exc:
            logger.error("Confident match processing failed", error=str(exc))
            # Fallback to LLM classification
            return self._process_llm_classification(text, metadata)
    
    def _process_llm_classification(self, text: str, metadata: EmailMetadata) -> ProcessedEmail:
        """Process email using LLM classification."""
        try:
            processed_email = self.llm_classifier.classify_email(text, metadata)
            
            # Extract user data
            processed_email.data = self._extract_user_data(text)
            
            logger.info("Processed using LLM classification",
                       category=processed_email.email_category.value,
                       confidence=processed_email.confidence_score)
            
            return processed_email
            
        except Exception as exc:
            logger.error("LLM classification failed", error=str(exc))
            raise
    
    def _extract_user_data(self, text: str) -> ExtractedData:
        """Extract user data from text."""
        try:
            pii_data = self.pii_processor.extract_pii_data(text)
            
            extracted_data = ExtractedData(
                email=pii_data.get('email', []),
                phone_number=pii_data.get('phone_number', []),
                credit_card_number=pii_data.get('credit_card_number', [])
            )
            
            logger.debug("User data extracted", 
                        emails=len(extracted_data.email or []),
                        phones=len(extracted_data.phone_number or []),
                        cards=len(extracted_data.credit_card_number or []))
            
            return extracted_data
            
        except Exception as exc:
            logger.error("User data extraction failed", error=str(exc))
            return ExtractedData()
    
    def _enhance_business_entity(self, processed_email: ProcessedEmail) -> ProcessedEmail:
        """Enhance business entity with DPO email if missing."""
        try:
            business_entity = processed_email.business_entity
            
            # If DPO email is missing and we have a website, try to scrape it
            if not business_entity.dpo_email and business_entity.website:
                logger.info("Attempting to scrape DPO email", website=business_entity.website)
                
                try:
                    # Run privacy policy scraper
                    scraper_result = self.privacy_scraper._run(str(business_entity.website))
                    
                    # Parse result (it's returned as JSON string)
                    import json
                    result_data = json.loads(scraper_result)
                    
                    if result_data.get('success') and result_data.get('dpo_email'):
                        business_entity.dpo_email = result_data['dpo_email']
                        logger.info("DPO email found via scraping", 
                                   dpo_email=business_entity.dpo_email)
                    
                except Exception as scrape_exc:
                    logger.warning("DPO email scraping failed", error=str(scrape_exc))
            
            return processed_email
            
        except Exception as exc:
            logger.error("Business entity enhancement failed", error=str(exc))
            return processed_email
    
    def _store_in_vector_db(self, text: str, processed_email: ProcessedEmail):
        """Store processed email in vector database."""
        try:
            doc_id = self.vector_store.add_email_embedding(
                email_content=text,
                metadata=processed_email.metadata,
                email_category=processed_email.email_category,
                business_entity=processed_email.business_entity,
                confidence_score=processed_email.confidence_score
            )
            
            logger.info("Email stored in vector database", doc_id=doc_id)
            
        except Exception as exc:
            logger.error("Failed to store in vector database", error=str(exc))
            # Don't raise - this is not critical for the main processing
