"""Privacy policy scraper tool for extracting DPO email addresses."""

import re
import asyncio
from typing import List, Optional
from urllib.parse import urljoin
import requests
from playwright.async_api import async_playwright
from langchain.tools import BaseTool

from pydantic import BaseModel, Field
import structlog

from app.models import PrivacyPolicyResult
from app.llm.chains import DPOExtractionChain

logger = structlog.get_logger()


class PrivacyPolicyScraperInput(BaseModel):
    """Input schema for privacy policy scraper tool."""
    website_url: str = Field(description="Website URL to scrape for privacy policy")


class PrivacyPolicyScraperTool(BaseTool):
    """LangChain tool for scraping privacy policies and extracting DPO emails."""

    name: str = "privacy_policy_scraper"
    description: str = "Scrapes privacy policy pages to extract Data Protection Officer (DPO) email addresses"
    args_schema: type[BaseModel] = PrivacyPolicyScraperInput
    dpo_chain: DPOExtractionChain = Field(default_factory=DPOExtractionChain)

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    

    
    def _run(self, website_url: str) -> str:
        """
        Run the privacy policy scraper synchronously.
        
        Args:
            website_url: Website URL to scrape
            
        Returns:
            JSON string with scraping results
        """
        try:
            # Run async scraper
            result = asyncio.run(self._scrape_privacy_policy(website_url))
            return result.model_dump_json()
            
        except Exception as exc:
            logger.error("Privacy policy scraping failed", url=website_url, error=str(exc))
            return PrivacyPolicyResult(
                success=False,
                error_message=str(exc)
            ).model_dump_json()
    

    async def _scrape_privacy_policy(self, website_url: str) -> PrivacyPolicyResult:
        """
        Scrape privacy policy and extract DPO email.
        
        Args:
            website_url: Website URL to scrape
            
        Returns:
            PrivacyPolicyResult with extraction results
        """
        try:
            # Find privacy policy URLs
            privacy_urls = await self._find_privacy_policy_urls(website_url)
            
            if not privacy_urls:
                return PrivacyPolicyResult(
                    success=False,
                    error_message="No privacy policy URLs found"
                )
            
            # Try to scrape each privacy policy URL
            for privacy_url in privacy_urls:
                try:
                    content = await self._scrape_page_content(privacy_url)
                    
                    if content:
                        # Extract DPO email using LLM
                        dpo_email = await self._extract_dpo_email(content)
                        
                        if dpo_email and dpo_email.lower() != "none":
                            return PrivacyPolicyResult(
                                dpo_email=dpo_email,
                                privacy_policy_url=privacy_url,
                                success=True
                            )
                
                except Exception as exc:
                    logger.warning("Failed to scrape privacy URL", 
                                 url=privacy_url, error=str(exc))
                    continue
            
            return PrivacyPolicyResult(
                success=False,
                error_message="No DPO email found in privacy policies"
            )
            
        except Exception as exc:
            logger.error("Privacy policy scraping failed", error=str(exc))
            return PrivacyPolicyResult(
                success=False,
                error_message=str(exc)
            )
    
    async def _find_privacy_policy_urls(self, website_url: str) -> List[str]:
        """
        Find potential privacy policy URLs for a website.
        
        Args:
            website_url: Base website URL
            
        Returns:
            List of potential privacy policy URLs
        """
        # Common privacy policy URL patterns
        privacy_paths = [
            '/privacy',
            '/privacy-policy',
            '/privacy_policy',
            '/privacypolicy',
            '/legal/privacy',
            '/terms/privacy',
            '/policy/privacy',
            '/privacy.html',
            '/privacy.php'
        ]
        
        # Normalize base URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Generate potential URLs
        privacy_urls = []
        for path in privacy_paths:
            privacy_url = urljoin(website_url, path)
            privacy_urls.append(privacy_url)
        
        # Try to find privacy policy links on the main page
        try:
            discovered_urls = await self._discover_privacy_links(website_url)
            privacy_urls.extend(discovered_urls)
        except Exception as exc:
            logger.warning("Failed to discover privacy links", error=str(exc))
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(privacy_urls))
    
    async def _discover_privacy_links(self, website_url: str) -> List[str]:
        """
        Discover privacy policy links from the main website.
        
        Args:
            website_url: Website URL to analyze
            
        Returns:
            List of discovered privacy policy URLs
        """
        discovered_urls = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to the website
                await page.goto(website_url, timeout=10000)
                
                # Look for privacy policy links
                privacy_selectors = [
                    'a[href*="privacy"]',
                    'a[href*="Privacy"]',
                    'a:has-text("Privacy Policy")',
                    'a:has-text("Privacy")',
                    'a:has-text("Data Protection")'
                ]
                
                for selector in privacy_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            href = await element.get_attribute('href')
                            if href:
                                full_url = urljoin(website_url, href)
                                discovered_urls.append(full_url)
                    except Exception:
                        continue
                
                await browser.close()
                
        except Exception as exc:
            logger.warning("Failed to discover privacy links with Playwright", error=str(exc))
        
        return discovered_urls
    
    async def _scrape_page_content(self, url: str) -> Optional[str]:
        """
        Scrape content from a privacy policy page.
        
        Args:
            url: Privacy policy URL
            
        Returns:
            Page content or None if failed
        """
        try:
            # First try with requests (faster)
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                
                if len(text) > 100:  # Ensure we got meaningful content
                    return text
            
        except Exception as exc:
            logger.warning("Requests scraping failed, trying Playwright", 
                         url=url, error=str(exc))
        
        # Fallback to Playwright for dynamic content
        try:
            async with async_playwright() as p:
                try:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    page = await browser.new_page()

                    await page.goto(url, timeout=15000)

                    # Wait for content to load
                    await page.wait_for_timeout(2000)

                    # Get text content
                    content = await page.inner_text('body')

                    await browser.close()

                    return content

                except Exception as browser_exc:
                    logger.warning("Playwright browser launch failed, trying fallback",
                                 error=str(browser_exc))
                    # Try with different browser options
                    try:
                        browser = await p.chromium.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                        )
                        page = await browser.new_page()
                        await page.goto(url, timeout=10000)
                        content = await page.inner_text('body')
                        await browser.close()
                        return content
                    except Exception:
                        logger.error("All Playwright options failed", url=url)
                        return None

        except Exception as exc:
            logger.error("Playwright scraping failed", url=url, error=str(exc))
            return None
    
    async def _extract_dpo_email(self, content: str) -> Optional[str]:
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

            # Use DPO extraction chain
            extracted_email = await self.dpo_chain.extract_dpo_email(content)

            if extracted_email:
                return extracted_email

            # Fallback: regex-based extraction
            return self._regex_extract_dpo_email(content)

        except Exception as exc:
            logger.error("LLM extraction failed, using regex fallback", error=str(exc))
            return self._regex_extract_dpo_email(content)
    
    def _regex_extract_dpo_email(self, content: str) -> Optional[str]:
        """
        Extract DPO email using regex patterns.
        
        Args:
            content: Privacy policy content
            
        Returns:
            DPO email address or None
        """
        # DPO-related patterns
        dpo_patterns = [
            r'(?:data\s+protection\s+officer|dpo)[\s\S]{0,100}?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\s\S]{0,50}?(?:data\s+protection|dpo)',
            r'privacy[\s\S]{0,100}?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\s\S]{0,50}?privacy'
        ]
        
        for pattern in dpo_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if self._is_valid_email(match):
                    return match
        
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
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
