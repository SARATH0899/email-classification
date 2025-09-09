"""LLM models and configurations."""

from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import structlog

from app.config import settings

logger = structlog.get_logger()

# Try to import Gemini (optional dependency)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini not available. Install langchain-google-genai to use Gemini models.")


class LLMModelManager:
    """Manager for different LLM models and configurations."""

    def __init__(self):
        """Initialize the LLM model manager."""
        self.models = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize available LLM models based on provider with fallback."""
        provider = settings.llm_provider.lower()
        logger.info("Initializing LLM models", provider=provider)

        # Try primary provider first
        try:
            if provider == "openai":
                self._initialize_openai_models()
            elif provider == "gemini":
                self._initialize_gemini_models()
            elif provider == "ollama":
                self._initialize_ollama_models()
            else:
                logger.warning(f"Unknown LLM provider: {provider}, trying fallbacks")
                raise ValueError(f"Unknown provider: {provider}")

            logger.info("LLM models initialized successfully", provider=provider)
            return

        except Exception as exc:
            logger.error("Failed to initialize primary LLM provider",
                        provider=provider, error=str(exc))

            # Try fallback providers
            fallback_providers = ['openai', 'gemini', 'ollama']
            if provider in fallback_providers:
                fallback_providers.remove(provider)

            for fallback_provider in fallback_providers:
                try:
                    logger.info("Trying fallback provider", fallback=fallback_provider)

                    if fallback_provider == "openai" and settings.openai_api_key:
                        self._initialize_openai_models()
                        logger.info("Fallback to OpenAI successful")
                        return
                    elif fallback_provider == "gemini" and settings.gemini_api_key:
                        self._initialize_gemini_models()
                        logger.info("Fallback to Gemini successful")
                        return
                    elif fallback_provider == "ollama":
                        self._initialize_ollama_models()
                        logger.info("Fallback to Ollama successful")
                        return

                except Exception as fallback_exc:
                    logger.warning("Fallback provider failed",
                                 provider=fallback_provider,
                                 error=str(fallback_exc))
                    continue

            # If all providers fail, create a mock model for testing
            logger.error("All LLM providers failed, creating mock model")
            self._create_mock_model()

    def _initialize_openai_models(self):
        """Initialize OpenAI models."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for OpenAI provider")

        # Primary model
        self.models['primary'] = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

        # Alternative models
        self.models['gpt-3.5-turbo'] = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name="gpt-3.5-turbo",
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

        self.models['gpt-4'] = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name="gpt-4",
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

    def _initialize_gemini_models(self):
        """Initialize Gemini models."""
        if not GEMINI_AVAILABLE:
            raise ImportError("Gemini not available. Install langchain-google-genai")

        if not settings.gemini_api_key:
            raise ValueError("Gemini API key is required for Gemini provider")

        # Primary model
        self.models['primary'] = ChatGoogleGenerativeAI(
            google_api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens
        )

        # Alternative models
        self.models['gemini-pro'] = ChatGoogleGenerativeAI(
            google_api_key=settings.gemini_api_key,
            model="gemini-pro",
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens
        )

    def _initialize_ollama_models(self):
        """Initialize Ollama models."""
        try:
            # Primary model
            self.models['primary'] = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=settings.llm_temperature
            )
            logger.info("Ollama primary model initialized",
                       base_url=settings.ollama_base_url,
                       model=settings.ollama_model)
        except Exception as exc:
            logger.error("Failed to initialize Ollama primary model",
                        base_url=settings.ollama_base_url,
                        model=settings.ollama_model,
                        error=str(exc))
            raise

        # Alternative models
        self.models['llama2'] = ChatOllama(
            base_url=settings.ollama_base_url,
            model="llama2",
            temperature=settings.llm_temperature
        )

        self.models['mistral'] = ChatOllama(
            base_url=settings.ollama_base_url,
            model="mistral",
            temperature=settings.llm_temperature
        )

    def _create_mock_model(self):
        """Create a mock model for testing when all providers fail."""
        from langchain.llms.fake import FakeListLLM

        # Create a fake LLM that returns predictable responses
        mock_responses = [
            '{"email_category": "marketing", "business_entity": {"name": "Unknown Company", "website": null, "industry": null, "location": null, "dpo_email": null}, "data": {"email": [], "phone_number": [], "credit_card_number": []}, "confidence_score": 0.5}',
            '{"email_category": "transactional", "business_entity": {"name": "Service Provider", "website": null, "industry": null, "location": null, "dpo_email": null}, "data": {"email": [], "phone_number": [], "credit_card_number": []}, "confidence_score": 0.6}',
            '{"email_category": "personal", "business_entity": {"name": "Personal Contact", "website": null, "industry": null, "location": null, "dpo_email": null}, "data": {"email": [], "phone_number": [], "credit_card_number": []}, "confidence_score": 0.7}'
        ]

        self.models['primary'] = FakeListLLM(responses=mock_responses)
        logger.warning("Using mock LLM model - responses will be simulated")
    
    def get_model(self, model_name: str = 'primary'):
        """
        Get a specific LLM model.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            LLM model instance
        """
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not found, using primary")
            model_name = 'primary'

        if model_name not in self.models:
            available_models = list(self.models.keys())
            raise ValueError(f"No models available. Requested: '{model_name}', Available: {available_models}")

        return self.models[model_name]
    
    def get_available_models(self) -> list:
        """Get list of available model names."""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information
        """
        if model_name not in self.models:
            return {"error": "Model not found"}
        
        model = self.models[model_name]
        
        return {
            "model_name": getattr(model, 'model_name', model_name),
            "temperature": getattr(model, 'temperature', None),
            "max_tokens": getattr(model, 'max_tokens', None),
            "type": type(model).__name__
        }


# Global model manager instance
model_manager = LLMModelManager()
