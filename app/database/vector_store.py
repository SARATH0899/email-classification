"""Vector store service using ChromaDB for similarity search."""

import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import structlog

from app.config import settings as app_settings
from app.models import EmailMetadata, BusinessEntity, EmailCategory

# Try to import additional embedding providers
try:
    from langchain_community.embeddings import OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = structlog.get_logger()


class VectorStoreService:
    """Service for managing vector embeddings and similarity search."""
    
    def __init__(self):
        """Initialize the vector store service."""
        self._initialize_chroma()
        self._initialize_embeddings()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Check if we should use external ChromaDB
            if app_settings.chromadb_use_external:
                # Connect to external ChromaDB server
                self.chroma_client = chromadb.HttpClient(
                    host=app_settings.chromadb_host,
                    port=app_settings.chromadb_port,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                logger.info("Connected to external ChromaDB",
                           host=app_settings.chromadb_host,
                           port=app_settings.chromadb_port)
            else:
                # Use local persistent client
                os.makedirs(app_settings.chroma_persist_directory, exist_ok=True)

                self.chroma_client = chromadb.PersistentClient(
                    path=app_settings.chroma_persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info("Using local ChromaDB",
                           persist_dir=app_settings.chroma_persist_directory)

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="email_embeddings",
                metadata={"description": "Email content embeddings for similarity search"}
            )

            logger.info("ChromaDB collection ready", collection_name="email_embeddings")
            
        except Exception as exc:
            logger.error("Failed to initialize ChromaDB", error=str(exc))
            raise
    
    def _initialize_embeddings(self):
        """Initialize embeddings based on LLM provider with fallback."""
        provider = app_settings.llm_provider.lower()
        logger.info("Initializing embeddings", provider=provider)

        # Try primary provider first
        try:
            if provider == "openai" and app_settings.openai_api_key:
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=app_settings.openai_api_key,
                    model="text-embedding-ada-002"
                )
                logger.info("OpenAI embeddings initialized successfully")
                return

            elif provider == "gemini" and GEMINI_AVAILABLE and app_settings.gemini_api_key:
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    google_api_key=app_settings.gemini_api_key,
                    model="models/embedding-001"
                )
                logger.info("Gemini embeddings initialized successfully")
                return

            elif provider == "ollama" and OLLAMA_AVAILABLE:
                self.embeddings = OllamaEmbeddings(
                    base_url=app_settings.ollama_base_url,
                    model="nomic-embed-text"
                )
                logger.info("Ollama embeddings initialized successfully")
                return
            else:
                raise ValueError(f"Primary provider {provider} not available or missing credentials")

        except Exception as exc:
            logger.warning("Primary embeddings provider failed",
                          provider=provider, error=str(exc))

        # Try fallback providers
        fallback_providers = [
            ("openai", app_settings.openai_api_key),
            ("gemini", app_settings.gemini_api_key and GEMINI_AVAILABLE),
            ("ollama", OLLAMA_AVAILABLE)
        ]

        for fallback_provider, available in fallback_providers:
            if fallback_provider == provider:
                continue  # Skip the one we already tried

            if not available:
                continue

            try:
                logger.info("Trying fallback embeddings provider", fallback=fallback_provider)

                if fallback_provider == "openai":
                    self.embeddings = OpenAIEmbeddings(
                        openai_api_key=app_settings.openai_api_key,
                        model="text-embedding-ada-002"
                    )
                    logger.info("Fallback to OpenAI embeddings successful")
                    return

                elif fallback_provider == "gemini":
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        google_api_key=app_settings.gemini_api_key,
                        model="models/embedding-001"
                    )
                    logger.info("Fallback to Gemini embeddings successful")
                    return

                elif fallback_provider == "ollama":
                    self.embeddings = OllamaEmbeddings(
                        base_url=app_settings.ollama_base_url,
                        model="nomic-embed-text"
                    )
                    logger.info("Fallback to Ollama embeddings successful")
                    return

            except Exception as fallback_exc:
                logger.warning("Fallback embeddings provider failed",
                             provider=fallback_provider, error=str(fallback_exc))
                continue

        # If all providers fail, create a mock embeddings service
        logger.error("All embeddings providers failed, creating mock embeddings")
        self._create_mock_embeddings()

    def _create_mock_embeddings(self):
        """Create a mock embeddings service when all providers fail."""
        from langchain.embeddings.fake import FakeEmbeddings

        # Create fake embeddings with consistent dimensions
        self.embeddings = FakeEmbeddings(size=1536)  # Same as OpenAI ada-002
        logger.warning("Using mock embeddings - similarity search will be simulated")
    
    def add_email_embedding(
        self,
        email_content: str,
        metadata: EmailMetadata,
        email_category: EmailCategory,
        business_entity: BusinessEntity,
        confidence_score: float
    ) -> str:
        """
        Add email embedding to the vector store.
        
        Args:
            email_content: Processed email content
            metadata: Email metadata
            email_category: Email category
            business_entity: Business entity information
            confidence_score: Processing confidence score
            
        Returns:
            Document ID in the vector store
        """
        try:
            # Create combined text for embedding
            combined_text = self._create_embedding_text(email_content, metadata)
            
            # Generate embedding
            embedding = self.embeddings.embed_query(combined_text)
            
            # Create document ID
            doc_id = str(uuid.uuid4())
            
            # Prepare metadata for storage
            doc_metadata = {
                "sender_domain": metadata.sender_domain,
                "email_category": email_category.value,
                "business_name": business_entity.name,
                "business_website": str(business_entity.website) if business_entity.website else None,
                "business_industry": business_entity.industry,
                "business_location": business_entity.location,
                "dpo_email": business_entity.dpo_email,
                "confidence_score": confidence_score,
                "urls_count": len(metadata.urls),
                "has_footer": bool(metadata.footer_text)
            }
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[combined_text],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            logger.info("Email embedding added", doc_id=doc_id, domain=metadata.sender_domain)
            
            return doc_id
            
        except Exception as exc:
            logger.error("Failed to add email embedding", error=str(exc))
            raise
    
    def search_similar_emails(
        self,
        query_content: str,
        query_metadata: EmailMetadata,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar emails in the vector store.
        
        Args:
            query_content: Query email content
            query_metadata: Query email metadata
            n_results: Number of results to return
            
        Returns:
            List of similar email matches with metadata
        """
        try:
            # Create combined text for query
            combined_text = self._create_embedding_text(query_content, query_metadata)
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(combined_text)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            matches = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    match = {
                        'id': doc_id,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    matches.append(match)
            
            logger.debug("Similar emails found", count=len(matches))
            
            return matches
            
        except Exception as exc:
            logger.error("Failed to search similar emails", error=str(exc))
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            stats = {
                "total_documents": count,
                "domains": set(),
                "categories": set(),
                "industries": set()
            }
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if metadata.get('sender_domain'):
                        stats['domains'].add(metadata['sender_domain'])
                    if metadata.get('email_category'):
                        stats['categories'].add(metadata['email_category'])
                    if metadata.get('business_industry'):
                        stats['industries'].add(metadata['business_industry'])
            
            # Convert sets to lists for JSON serialization
            stats['domains'] = list(stats['domains'])
            stats['categories'] = list(stats['categories'])
            stats['industries'] = list(stats['industries'])
            
            return stats
            
        except Exception as exc:
            logger.error("Failed to get collection stats", error=str(exc))
            return {"total_documents": 0, "domains": [], "categories": [], "industries": []}
    
    def _create_embedding_text(self, email_content: str, metadata: EmailMetadata) -> str:
        """
        Create combined text for embedding generation.
        
        Args:
            email_content: Email content
            metadata: Email metadata
            
        Returns:
            Combined text for embedding
        """
        # Combine email content with metadata
        parts = [email_content]
        
        # Add domain information
        parts.append(f"Domain: {metadata.sender_domain}")
        
        # Add footer if available
        if metadata.footer_text:
            parts.append(f"Footer: {metadata.footer_text}")
        
        # Add URL information
        if metadata.urls:
            url_domains = []
            for url in metadata.urls:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    if domain:
                        url_domains.append(domain)
                except:
                    continue
            
            if url_domains:
                parts.append(f"URL domains: {', '.join(set(url_domains))}")
        
        return "\n".join(parts)
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.info("Document deleted", doc_id=doc_id)
            return True
            
        except Exception as exc:
            logger.error("Failed to delete document", doc_id=doc_id, error=str(exc))
            return False
    
    def reset_collection(self) -> bool:
        """
        Reset the entire collection (delete all documents).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.chroma_client.delete_collection("email_embeddings")
            self.collection = self.chroma_client.create_collection(
                name="email_embeddings",
                metadata={"description": "Email content embeddings for similarity search"}
            )
            logger.warning("Collection reset - all documents deleted")
            return True
            
        except Exception as exc:
            logger.error("Failed to reset collection", error=str(exc))
            return False
