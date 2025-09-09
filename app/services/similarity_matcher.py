"""Confidence-based similarity matching service."""

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import structlog

from app.config import settings
from app.models import EmailMetadata, VectorMatch, BusinessEntity, EmailCategory
from app.database.vector_store import VectorStoreService

logger = structlog.get_logger()


class SimilarityMatcher:
    """Service for confidence-based vector similarity matching."""
    
    def __init__(self):
        """Initialize the similarity matcher."""
        try:
            self.vector_store = VectorStoreService()
            logger.info("Similarity matcher initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize vector store for similarity matching", error=str(exc))
            self.vector_store = None
    
    def find_best_match(
        self,
        email_content: str,
        metadata: EmailMetadata,
        n_candidates: int = 10
    ) -> Optional[VectorMatch]:
        """
        Find the best matching email with confidence scoring.
        
        Args:
            email_content: Query email content
            metadata: Query email metadata
            n_candidates: Number of candidates to consider
            
        Returns:
            Best vector match or None if no confident match found
        """
        try:
            # Check if vector store is available
            if not self.vector_store:
                logger.warning("Vector store not available, skipping similarity search")
                return None

            # Search for similar emails
            candidates = self.vector_store.search_similar_emails(
                email_content, metadata, n_candidates
            )
            
            if not candidates:
                logger.debug("No candidates found in vector search")
                return None
            
            # Calculate confidence scores for each candidate
            scored_matches = []
            for candidate in candidates:
                confidence_match = self._calculate_confidence_score(
                    candidate, metadata
                )
                if confidence_match:
                    scored_matches.append(confidence_match)
            
            if not scored_matches:
                logger.debug("No confident matches found")
                return None
            
            # Sort by confidence score and return the best match
            best_match = max(scored_matches, key=lambda x: x.confidence_score)
            
            logger.info(
                "Best match found",
                confidence=best_match.confidence_score,
                similarity=best_match.similarity_score,
                domain_weight=best_match.domain_weight
            )
            
            return best_match
            
        except Exception as exc:
            logger.error("Failed to find best match", error=str(exc))
            return None
    
    def _calculate_confidence_score(
        self,
        candidate: Dict[str, Any],
        query_metadata: EmailMetadata
    ) -> Optional[VectorMatch]:
        """
        Calculate confidence score for a candidate match.
        
        Args:
            candidate: Candidate match from vector search
            query_metadata: Query email metadata
            
        Returns:
            VectorMatch with confidence score or None
        """
        try:
            # Get similarity score (cosine similarity)
            similarity_score = candidate.get('similarity', 0.0)
            
            # Get candidate metadata
            candidate_metadata = candidate.get('metadata', {})
            candidate_domain = candidate_metadata.get('sender_domain', '')
            
            # Calculate domain matching weight
            domain_weight = self._calculate_domain_weight(
                query_metadata.sender_domain,
                candidate_domain
            )
            
            # Calculate final confidence score
            confidence_score = similarity_score * domain_weight
            
            # Create VectorMatch object
            vector_match = VectorMatch(
                similarity_score=similarity_score,
                domain_weight=domain_weight,
                confidence_score=confidence_score,
                metadata=candidate_metadata
            )
            
            logger.debug(
                "Confidence calculated",
                similarity=similarity_score,
                domain_weight=domain_weight,
                confidence=confidence_score,
                query_domain=query_metadata.sender_domain,
                candidate_domain=candidate_domain
            )
            
            return vector_match
            
        except Exception as exc:
            logger.error("Failed to calculate confidence score", error=str(exc))
            return None
    
    def _calculate_domain_weight(self, query_domain: str, candidate_domain: str) -> float:
        """
        Calculate domain matching weight based on domain similarity.
        
        Args:
            query_domain: Query email domain
            candidate_domain: Candidate email domain
            
        Returns:
            Domain weight (1.0 for exact, 0.8 for similar, 0.5 for different)
        """
        if not query_domain or not candidate_domain:
            return settings.default_domain_weight
        
        query_domain = query_domain.lower().strip()
        candidate_domain = candidate_domain.lower().strip()
        
        # Exact match
        if query_domain == candidate_domain:
            return settings.exact_domain_weight
        
        # Check for similar domains (subdomains, etc.)
        if self._are_domains_similar(query_domain, candidate_domain):
            return settings.similar_domain_weight
        
        # Different domains
        return settings.default_domain_weight
    
    def _are_domains_similar(self, domain1: str, domain2: str) -> bool:
        """
        Check if two domains are similar (e.g., subdomains of the same parent).
        
        Args:
            domain1: First domain
            domain2: Second domain
            
        Returns:
            True if domains are similar
        """
        try:
            # Extract root domains
            root1 = self._extract_root_domain(domain1)
            root2 = self._extract_root_domain(domain2)
            
            # Check if root domains match
            if root1 == root2:
                return True
            
            # Check if one is a subdomain of the other
            if domain1.endswith('.' + domain2) or domain2.endswith('.' + domain1):
                return True
            
            # Check for common patterns (mail.domain.com vs domain.com)
            common_prefixes = ['mail', 'email', 'smtp', 'noreply', 'no-reply']
            
            for prefix in common_prefixes:
                if (domain1.startswith(f"{prefix}.") and domain1[len(prefix)+1:] == domain2) or \
                   (domain2.startswith(f"{prefix}.") and domain2[len(prefix)+1:] == domain1):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _extract_root_domain(self, domain: str) -> str:
        """
        Extract root domain from a full domain.
        
        Args:
            domain: Full domain name
            
        Returns:
            Root domain
        """
        try:
            # Split domain parts
            parts = domain.split('.')
            
            # For domains like 'mail.google.com', return 'google.com'
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            
            return domain
            
        except Exception:
            return domain
    
    def is_confident_match(self, vector_match: VectorMatch) -> bool:
        """
        Check if a vector match meets the confidence threshold.
        
        Args:
            vector_match: Vector match to evaluate
            
        Returns:
            True if match is confident enough
        """
        return vector_match.confidence_score > settings.confidence_threshold
    
    def extract_business_entity_from_match(self, vector_match: VectorMatch) -> BusinessEntity:
        """
        Extract business entity information from a confident match.
        
        Args:
            vector_match: Confident vector match
            
        Returns:
            BusinessEntity object
        """
        try:
            metadata = vector_match.metadata
            
            business_entity = BusinessEntity(
                name=metadata.get('business_name', 'Unknown'),
                website=metadata.get('business_website'),
                dpo_email=metadata.get('dpo_email'),
                industry=metadata.get('business_industry'),
                location=metadata.get('business_location')
            )
            
            return business_entity
            
        except Exception as exc:
            logger.error("Failed to extract business entity from match", error=str(exc))
            # Return minimal business entity
            return BusinessEntity(name="Unknown")
    
    def get_email_category_from_match(self, vector_match: VectorMatch) -> EmailCategory:
        """
        Extract email category from a confident match.
        
        Args:
            vector_match: Confident vector match
            
        Returns:
            EmailCategory enum value
        """
        try:
            category_str = vector_match.metadata.get('email_category', 'personal')
            return EmailCategory(category_str)
            
        except (ValueError, KeyError):
            logger.warning("Invalid email category in match, defaulting to personal")
            return EmailCategory.PERSONAL
    
    def get_match_statistics(self, matches: List[VectorMatch]) -> Dict[str, Any]:
        """
        Get statistics about a set of matches.
        
        Args:
            matches: List of vector matches
            
        Returns:
            Dictionary with match statistics
        """
        if not matches:
            return {
                "total_matches": 0,
                "confident_matches": 0,
                "avg_confidence": 0.0,
                "avg_similarity": 0.0,
                "domain_distribution": {}
            }
        
        confident_matches = [m for m in matches if self.is_confident_match(m)]
        
        # Calculate averages
        avg_confidence = sum(m.confidence_score for m in matches) / len(matches)
        avg_similarity = sum(m.similarity_score for m in matches) / len(matches)
        
        # Domain distribution
        domain_dist = {}
        for match in matches:
            domain = match.metadata.get('sender_domain', 'unknown')
            domain_dist[domain] = domain_dist.get(domain, 0) + 1
        
        return {
            "total_matches": len(matches),
            "confident_matches": len(confident_matches),
            "avg_confidence": round(avg_confidence, 3),
            "avg_similarity": round(avg_similarity, 3),
            "domain_distribution": domain_dist
        }
