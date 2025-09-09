"""Metadata extraction service for email processing."""

import re
from typing import List, Optional
from urllib.parse import urlparse
import structlog

from app.models import EmailInput, EmailMetadata
from app.processing.html_processor import HTMLProcessor
from app.config import settings

logger = structlog.get_logger()


class MetadataExtractor:
    """Service for extracting metadata from email content."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.html_processor = HTMLProcessor()
    
    def extract_metadata(self, email: EmailInput, clean_text: str) -> EmailMetadata:
        """
        Extract comprehensive metadata from email.
        
        Args:
            email: Email input data
            clean_text: Cleaned text content
            
        Returns:
            EmailMetadata object with extracted information
        """
        try:
            # Extract sender domain
            sender_domain = self.extract_sender_domain(email.from_email)
            
            # Extract URLs from HTML content
            urls = []
            if email.html_content:
                urls.extend(self.html_processor.extract_urls(email.html_content))
            
            # Also extract URLs from text content
            text_urls = self.extract_urls_from_text(clean_text)
            urls.extend(text_urls)
            
            # Remove duplicates while preserving order
            urls = list(dict.fromkeys(urls))
            
            # Extract footer text
            footer_text = None
            if email.html_content:
                footer_text = self.html_processor.extract_footer_text(
                    email.html_content, 
                    settings.footer_lines_count
                )
            
            # Fallback to text-based footer extraction
            if not footer_text:
                footer_text = self.extract_footer_from_text(
                    clean_text, 
                    settings.footer_lines_count
                )
            
            metadata = EmailMetadata(
                sender_domain=sender_domain,
                footer_text=footer_text,
                urls=urls
            )
            
            logger.debug(
                "Metadata extracted",
                sender_domain=sender_domain,
                urls_count=len(urls),
                has_footer=bool(footer_text)
            )
            
            return metadata
            
        except Exception as exc:
            logger.error("Metadata extraction failed", error=str(exc))
            # Return minimal metadata
            return EmailMetadata(
                sender_domain=self.extract_sender_domain(email.from_email),
                urls=[]
            )
    
    def extract_sender_domain(self, email_address: str) -> str:
        """
        Extract domain from email address.
        
        Args:
            email_address: Email address string
            
        Returns:
            Domain part of the email address
        """
        try:
            # Split email address and get domain part
            domain = email_address.split('@')[1].lower()
            return domain
        except (IndexError, AttributeError):
            logger.warning("Failed to extract domain from email", email=email_address)
            return "unknown"
    
    def extract_urls_from_text(self, text: str) -> List[str]:
        """
        Extract URLs from plain text using regex.
        
        Args:
            text: Plain text content
            
        Returns:
            List of URLs found in text
        """
        if not text:
            return []
        
        # URL regex pattern
        url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'.,)]'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        # Validate and clean URLs
        valid_urls = []
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    valid_urls.append(url)
            except Exception:
                continue
        
        return valid_urls
    
    def extract_footer_from_text(self, text: str, lines_count: int = 3) -> Optional[str]:
        """
        Extract footer text from plain text content.
        
        Args:
            text: Plain text content
            lines_count: Number of lines to consider as footer
            
        Returns:
            Footer text or None if not found
        """
        if not text:
            return None
        
        try:
            lines = text.split('\n')
            
            # Filter out empty lines
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            if len(non_empty_lines) >= lines_count:
                footer_lines = non_empty_lines[-lines_count:]
                footer_text = '\n'.join(footer_lines)
                
                # Check if footer looks like actual footer content
                if self._is_likely_footer(footer_text):
                    return footer_text
            
            return None
            
        except Exception as exc:
            logger.error("Failed to extract footer from text", error=str(exc))
            return None
    
    def _is_likely_footer(self, text: str) -> bool:
        """
        Determine if text is likely to be footer content.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if text appears to be footer content
        """
        footer_indicators = [
            'unsubscribe',
            'privacy policy',
            'terms of service',
            'contact us',
            'copyright',
            '©',
            'all rights reserved',
            'company',
            'address',
            'phone',
            'email'
        ]
        
        text_lower = text.lower()
        
        # Check for footer indicators
        indicator_count = sum(1 for indicator in footer_indicators if indicator in text_lower)
        
        # Check for email addresses or URLs (common in footers)
        has_email = '@' in text
        has_url = 'http' in text_lower
        
        # Consider it a footer if it has multiple indicators or contains contact info
        return indicator_count >= 2 or has_email or has_url
    
    def extract_company_info(self, text: str) -> dict:
        """
        Extract potential company information from text.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary with potential company information
        """
        company_info = {
            'potential_company_names': [],
            'addresses': [],
            'phone_numbers': [],
            'websites': []
        }
        
        try:
            # Extract potential company names (capitalized words/phrases)
            company_pattern = r'\b[A-Z][a-zA-Z\s&.,]+(?:Inc|LLC|Corp|Company|Ltd|Limited)\b'
            companies = re.findall(company_pattern, text)
            company_info['potential_company_names'] = list(set(companies))
            
            # Extract addresses (basic pattern)
            address_pattern = r'\d+\s+[A-Za-z\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)'
            addresses = re.findall(address_pattern, text, re.IGNORECASE)
            company_info['addresses'] = list(set(addresses))
            
            # Extract phone numbers (basic pattern)
            phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
            phones = re.findall(phone_pattern, text)
            company_info['phone_numbers'] = list(set(phones))
            
            # Extract websites
            company_info['websites'] = self.extract_urls_from_text(text)
            
            return company_info
            
        except Exception as exc:
            logger.error("Failed to extract company info", error=str(exc))
            return company_info
