"""Pydantic models for the email processing application."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from enum import Enum


class EmailCategory(str, Enum):
    """Email category enumeration."""
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    SURVEY = "survey"
    PERSONAL = "personal"
    CUSTOMER_SUPPORT = "customer_support"


class EmailInput(BaseModel):
    """Input email structure."""
    from_email: EmailStr = Field(..., alias="from")
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None


class BusinessEntity(BaseModel):
    """Business entity information."""
    name: str
    website: Optional[HttpUrl] = None
    dpo_email: Optional[EmailStr] = None
    industry: Optional[str] = None
    location: Optional[str] = None


class ExtractedData(BaseModel):
    """Extracted user data from email."""
    email: Optional[List[str]] = None
    phone_number: Optional[List[str]] = None
    credit_card_number: Optional[List[str]] = None
    # Add more fields as needed


class EmailMetadata(BaseModel):
    """Email metadata extracted during processing."""
    sender_domain: str
    footer_text: Optional[str] = None
    urls: List[str] = Field(default_factory=list)


class ProcessedEmail(BaseModel):
    """Final processed email result."""
    email_category: EmailCategory
    business_entity: BusinessEntity
    data: ExtractedData
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[EmailMetadata] = None
    processed_at: Optional[str] = None


class VectorMatch(BaseModel):
    """Vector similarity match result."""
    similarity_score: float
    domain_weight: float
    confidence_score: float
    metadata: Dict[str, Any]


class PrivacyPolicyResult(BaseModel):
    """Result from privacy policy scraping."""
    dpo_email: Optional[EmailStr] = None
    privacy_policy_url: Optional[HttpUrl] = None
    success: bool = False
    error_message: Optional[str] = None
