"""LangChain chains for email processing."""

from typing import Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field
import structlog

from app.models import EmailCategory, BusinessEntity, ExtractedData, ProcessedEmail, EmailMetadata
from app.llm.models import model_manager
from app.prompts import email_classification, dpo_extraction

logger = structlog.get_logger()


class EmailClassificationResult(BaseModel):
    """Pydantic model for LLM classification output."""
    email_category: EmailCategory = Field(description="Category of the email")
    business_entity: BusinessEntity = Field(description="Business entity information")
    data: ExtractedData = Field(description="Extracted user data")
    confidence_score: float = Field(description="Classification confidence score", ge=0.0, le=1.0)


class EmailClassificationChain:
    """Chain for email classification and business entity extraction."""

    def __init__(self, model_name: str = 'primary'):
        """Initialize the classification chain."""
        self.model_name = model_name
        try:
            self.llm = model_manager.get_model(model_name)
            # Log the actual model details
            model_info = getattr(self.llm, 'model', 'unknown')
            provider_info = getattr(self.llm, 'base_url', getattr(self.llm, 'model_name', 'unknown'))
            logger.info("LLM model initialized",
                       model_name=model_name,
                       model_info=model_info,
                       provider_info=provider_info)
        except Exception as exc:
            logger.error("Failed to initialize LLM model",
                        model_name=model_name,
                        error=str(exc))
            raise
        self._initialize_parser()
        self._create_chain()
    
    def _initialize_parser(self):
        """Initialize the Pydantic output parser."""
        try:
            self.output_parser = PydanticOutputParser(pydantic_object=EmailClassificationResult)
            logger.info("Pydantic output parser initialized")
            
        except Exception as exc:
            logger.error("Failed to initialize output parser", error=str(exc))
            raise
    
    def _create_chain(self):
        """Create the LangChain classification chain."""
        try:
            # Create the prompt template using separated prompts
            self.prompt_template = ChatPromptTemplate.from_messages([
                ("system", email_classification.SYSTEM_PROMPT),
                ("human", email_classification.HUMAN_PROMPT)
            ])

            # Create the chain
            self.classification_chain = self.prompt_template | self.llm | self.output_parser

            logger.info("Classification chain created successfully", model=self.model_name)

        except Exception as exc:
            logger.error("Failed to create classification chain", error=str(exc))
            raise
    
    def classify_email(
        self,
        email_content: str,
        metadata: EmailMetadata
    ) -> ProcessedEmail:
        """
        Classify email and extract business entity information using LLM.
        
        Args:
            email_content: Cleaned email content
            metadata: Email metadata
            
        Returns:
            ProcessedEmail with classification results
        """
        try:
            # Prepare input for the LLM
            input_data = {
                "email_content": email_content,
                "sender_domain": metadata.sender_domain,
                "footer_text": metadata.footer_text or "No footer",
                "urls": ", ".join(metadata.urls) if metadata.urls else "No URLs",
                "format_instructions": self.output_parser.get_format_instructions()
            }
            
            logger.info("Starting LLM classification",
                       domain=metadata.sender_domain,
                       model=self.model_name,
                       model_type=type(self.llm).__name__)

            # Run the classification chain
            result = self.classification_chain.invoke(input_data)
            
            # Create ProcessedEmail object
            processed_email = ProcessedEmail(
                email_category=result.email_category,
                business_entity=result.business_entity,
                data=result.data,
                confidence_score=result.confidence_score,
                metadata=metadata
            )
            
            logger.info(
                "LLM classification completed",
                category=result.email_category.value,
                business=result.business_entity.name,
                confidence=result.confidence_score,
                model=self.model_name
            )
            
            return processed_email
            
        except Exception as exc:
            logger.error("LLM classification failed", error=str(exc), model=self.model_name)
            # Return fallback result
            return self._create_fallback_result(email_content, metadata)
    

    
    def _create_fallback_result(self, email_content: str, metadata: EmailMetadata) -> ProcessedEmail:
        """
        Create a fallback result when LLM classification fails.
        
        Args:
            email_content: Email content
            metadata: Email metadata
            
        Returns:
            Fallback ProcessedEmail result
        """
        try:
            # Simple heuristic-based classification
            category = self._heuristic_classification(email_content, metadata)
            
            # Extract basic business entity info
            business_entity = BusinessEntity(
                name=self._extract_company_name_heuristic(email_content, metadata),
                website=metadata.urls[0] if metadata.urls else None,
                industry=None,
                location=None,
                dpo_email=None
            )
            
            # Basic data extraction (empty for fallback)
            extracted_data = ExtractedData()
            
            return ProcessedEmail(
                email_category=category,
                business_entity=business_entity,
                data=extracted_data,
                confidence_score=0.3,  # Low confidence for fallback
                metadata=metadata
            )
            
        except Exception as exc:
            logger.error("Fallback result creation failed", error=str(exc))
            # Ultimate fallback
            return ProcessedEmail(
                email_category=EmailCategory.PERSONAL,
                business_entity=BusinessEntity(name="Unknown"),
                data=ExtractedData(),
                confidence_score=0.1,
                metadata=metadata
            )
    
    def _heuristic_classification(self, content: str, metadata: EmailMetadata) -> EmailCategory:
        """Simple heuristic-based email classification."""
        content_lower = content.lower()
        
        # Marketing indicators
        marketing_keywords = ['unsubscribe', 'newsletter', 'promotion', 'offer', 'sale', 'discount']
        if any(keyword in content_lower for keyword in marketing_keywords):
            return EmailCategory.MARKETING
        
        # Transactional indicators
        transactional_keywords = ['order', 'receipt', 'confirmation', 'invoice', 'payment', 'account']
        if any(keyword in content_lower for keyword in transactional_keywords):
            return EmailCategory.TRANSACTIONAL
        
        # Survey indicators
        survey_keywords = ['survey', 'feedback', 'questionnaire', 'rate', 'review']
        if any(keyword in content_lower for keyword in survey_keywords):
            return EmailCategory.SURVEY
        
        # Customer support indicators
        support_keywords = ['support', 'help', 'ticket', 'issue', 'problem', 'assistance']
        if any(keyword in content_lower for keyword in support_keywords):
            return EmailCategory.CUSTOMER_SUPPORT
        
        # Default to personal
        return EmailCategory.PERSONAL
    
    def _extract_company_name_heuristic(self, content: str, metadata: EmailMetadata) -> str:
        """Extract company name using simple heuristics."""
        # Try to extract from domain
        domain_parts = metadata.sender_domain.split('.')
        if len(domain_parts) >= 2:
            company_name = domain_parts[-2].capitalize()
            return company_name
        
        return "Unknown Company"


class DPOExtractionChain:
    """Chain for extracting DPO email from privacy policy content."""

    def __init__(self, model_name: str = 'primary'):
        """Initialize the DPO extraction chain."""
        self.model_name = model_name
        self.llm = model_manager.get_model(model_name)
        self._create_chain()

    def _create_chain(self):
        """Create the DPO extraction chain using separated prompts."""
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", dpo_extraction.SYSTEM_PROMPT),
            ("human", dpo_extraction.HUMAN_PROMPT)
        ])

        self.extraction_chain = self.extraction_prompt | self.llm
    
    async def extract_dpo_email(self, content: str) -> Optional[str]:
        """
        Extract DPO email from privacy policy content using LLM.
        
        Args:
            content: Privacy policy content
            
        Returns:
            DPO email address or None
        """
        try:
            # Truncate content if too long
            if len(content) > 8000:
                content = content[:8000] + "..."
            
            # Use LLM to extract DPO email
            response = await self.extraction_chain.ainvoke({
                "privacy_policy_text": content
            })
            
            extracted_text = response.content.strip()
            
            # Validate extracted email
            if self._is_valid_email(extracted_text):
                return extracted_text
            
            return None
            
        except Exception as exc:
            logger.error("LLM DPO extraction failed", error=str(exc))
            return None
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format
        """
        if not email or email.lower() == "none":
            return False
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
