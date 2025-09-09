"""HTML processing and content extraction service."""

import re
from typing import Optional, List
from bs4 import BeautifulSoup, Comment
import structlog

logger = structlog.get_logger()


class HTMLProcessor:
    """Service for processing HTML content and extracting clean text."""
    
    def __init__(self):
        """Initialize the HTML processor."""
        self.soup_parser = "lxml"
    
    def strip_html(self, html_content: str) -> str:
        """
        Strip HTML tags and return clean text.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Clean text content
        """
        if not html_content:
            return ""
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, self.soup_parser)
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove comments
            comments = soup.findAll(text=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            
            # Get text and clean it
            text = soup.get_text()
            
            # Clean up whitespace
            text = self._clean_whitespace(text)
            
            logger.debug("HTML stripped successfully", original_length=len(html_content), clean_length=len(text))
            
            return text
            
        except Exception as exc:
            logger.error("Failed to strip HTML", error=str(exc))
            # Fallback: use regex to remove basic HTML tags
            return self._fallback_html_strip(html_content)
    
    def extract_urls(self, html_content: str) -> List[str]:
        """
        Extract all URLs from HTML content.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            List of URLs found in the content
        """
        urls = []
        
        if not html_content:
            return urls
        
        try:
            soup = BeautifulSoup(html_content, self.soup_parser)
            
            # Extract URLs from href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith(('http://', 'https://')):
                    urls.append(href)
            
            # Extract URLs from src attributes (images, etc.)
            for element in soup.find_all(['img', 'iframe', 'embed'], src=True):
                src = element['src']
                if src.startswith(('http://', 'https://')):
                    urls.append(src)
            
            # Remove duplicates while preserving order
            urls = list(dict.fromkeys(urls))
            
            logger.debug("URLs extracted", count=len(urls))
            
            return urls
            
        except Exception as exc:
            logger.error("Failed to extract URLs", error=str(exc))
            # Fallback: use regex to find URLs
            return self._fallback_url_extraction(html_content)
    
    def extract_footer_text(self, html_content: str, lines_count: int = 3) -> Optional[str]:
        """
        Extract footer text from HTML content.
        
        Args:
            html_content: Raw HTML content
            lines_count: Number of lines to consider as footer
            
        Returns:
            Footer text or None if not found
        """
        if not html_content:
            return None
        
        try:
            # First try to find actual footer elements
            soup = BeautifulSoup(html_content, self.soup_parser)
            
            # Look for footer-related elements
            footer_elements = soup.find_all(['footer', 'div'], 
                                          class_=re.compile(r'footer|bottom|signature', re.I))
            
            if footer_elements:
                footer_text = footer_elements[-1].get_text().strip()
                if footer_text:
                    return self._clean_whitespace(footer_text)
            
            # Fallback: get last N lines of text content
            clean_text = self.strip_html(html_content)
            lines = clean_text.split('\n')
            
            # Filter out empty lines
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            if len(non_empty_lines) >= lines_count:
                footer_lines = non_empty_lines[-lines_count:]
                return '\n'.join(footer_lines)
            
            return None
            
        except Exception as exc:
            logger.error("Failed to extract footer text", error=str(exc))
            return None
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace in text."""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def _fallback_html_strip(self, html_content: str) -> str:
        """Fallback method to strip HTML using regex."""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html_content)
        # Clean whitespace
        clean = self._clean_whitespace(clean)
        return clean
    
    def _fallback_url_extraction(self, content: str) -> List[str]:
        """Fallback method to extract URLs using regex."""
        url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'.,)]'
        urls = re.findall(url_pattern, content)
        return list(dict.fromkeys(urls))  # Remove duplicates
