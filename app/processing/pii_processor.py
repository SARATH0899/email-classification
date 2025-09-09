"""PII detection and anonymization service using SpaCy and Presidio."""

import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import spacy
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import structlog

from app.config import settings

logger = structlog.get_logger()


class PIIProcessor:
    """Service for detecting and anonymizing PII in text content."""
    
    def __init__(self):
        """Initialize the PII processor with SpaCy and Presidio."""
        self._load_configuration()
        self._initialize_nlp_engine()
        self._initialize_presidio()

    def _load_configuration(self):
        """Load Presidio configuration."""
        config_path = Path(__file__).parent.parent / "config" / "presidio_config.yaml"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                logger.info("Presidio configuration loaded", config_path=str(config_path))
            except Exception as exc:
                logger.warning("Failed to load Presidio config, using defaults", error=str(exc))
                self.config = self._get_default_config()
        else:
            logger.info("Presidio config file not found, using defaults")
            self.config = self._get_default_config()

    def _get_default_config(self):
        """Get default Presidio configuration."""
        return {
            'nlp_engine_name': 'spacy',
            'models': [{'lang_code': 'en', 'model_name': 'en_core_web_sm'}],
            'ner_model_configuration': {
                'model_to_presidio_entity_mapping': {
                    'PERSON': 'PERSON',
                    'PER': 'PERSON',
                    'ORG': 'ORGANIZATION',
                    'GPE': 'LOCATION',
                    'LOC': 'LOCATION',
                    'NORP': 'NRP',
                    'FACILITY': 'LOCATION',
                    'EVENT': 'EVENT',
                    'FAC': 'LOCATION',
                    'PRODUCT': 'PRODUCT',
                    'WORK_OF_ART': 'PRODUCT',
                    'LAW': 'LAW',
                    'LANGUAGE': 'LANGUAGE',
                    'DATE': 'DATE_TIME',
                    'TIME': 'DATE_TIME',
                    'PERCENT': 'PERCENT',
                    'MONEY': 'MONEY',
                    'QUANTITY': 'QUANTITY',
                    'ORDINAL': 'ORDINAL',
                    'CARDINAL': 'CARDINAL'
                },
                'low_score_entity_names': [
                    'PERSON',
                    'ORGANIZATION',
                    'LOCATION'
                ],
                'labels_to_ignore': ['O']
            },
            'thresholds': {'default_score_threshold': 0.35}
        }

    def _initialize_nlp_engine(self):
        """Initialize NLP engine with proper configuration."""
        try:
            # Configure NLP engine provider with full configuration
            nlp_configuration = {
                "nlp_engine_name": self.config.get('nlp_engine_name', 'spacy'),
                "models": self.config.get('models', [{'lang_code': 'en', 'model_name': 'en_core_web_sm'}])
            }

            # Add NER model configuration if available
            if 'ner_model_configuration' in self.config:
                nlp_configuration.update(self.config['ner_model_configuration'])

            nlp_engine_provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
            self.nlp_engine = nlp_engine_provider.create_engine()

            # Also load SpaCy model directly for compatibility
            model_name = self.config['models'][0]['model_name']
            self.nlp = spacy.load(model_name)

            logger.info("NLP engine initialized successfully",
                       model=model_name,
                       has_ner_config='ner_model_configuration' in self.config)

        except OSError as exc:
            logger.error("SpaCy model not found", model=model_name, error=str(exc))
            # Fallback to smaller model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Fallback to en_core_web_sm model")
            except OSError:
                logger.error("No SpaCy model available. Please install: python -m spacy download en_core_web_sm")
                raise
        except Exception as exc:
            logger.error("Failed to initialize NLP engine", error=str(exc))
            raise

    def _initialize_presidio(self):
        """Initialize Presidio analyzer and anonymizer with configuration."""
        try:
            # Initialize analyzer with custom NLP engine
            self.analyzer = AnalyzerEngine(
                nlp_engine=self.nlp_engine,
                default_score_threshold=self.config.get('thresholds', {}).get('default_score_threshold', 0.35)
            )

            self.anonymizer = AnonymizerEngine()
            logger.info("Presidio engines initialized successfully")

        except Exception as exc:
            logger.error("Failed to initialize Presidio", error=str(exc))
            # Fallback to basic initialization
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                logger.info("Presidio engines initialized with fallback configuration")
            except Exception as fallback_exc:
                logger.error("Failed to initialize Presidio even with fallback", error=str(fallback_exc))
                raise
    
    def detect_pii(self, text: str, entities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Detect PII entities in text.
        
        Args:
            text: Text content to analyze
            entities: List of entity types to detect (None for all)
            
        Returns:
            List of detected PII entities with metadata
        """
        if not text:
            return []
        
        entities = entities or settings.pii_entities
        
        try:
            # Analyze text with Presidio
            results = self.analyzer.analyze(
                text=text,
                entities=entities,
                language='en'
            )
            
            # Convert to dict format
            pii_entities = []
            for result in results:
                pii_entities.append({
                    'entity_type': result.entity_type,
                    'start': result.start,
                    'end': result.end,
                    'score': result.score,
                    'text': text[result.start:result.end]
                })
            
            logger.debug("PII detection completed", entities_found=len(pii_entities))
            
            return pii_entities
            
        except Exception as exc:
            logger.error("PII detection failed", error=str(exc))
            return []
    
    def anonymize_text(self, text: str, entities: Optional[List[str]] = None) -> str:
        """
        Anonymize PII in text by masking with configured character.
        
        Args:
            text: Text content to anonymize
            entities: List of entity types to anonymize (None for all)
            
        Returns:
            Anonymized text content
        """
        if not text:
            return text
        
        entities = entities or settings.pii_entities
        
        try:
            # Analyze text first
            analyzer_results = self.analyzer.analyze(
                text=text,
                entities=entities,
                language='en'
            )
            
            if not analyzer_results:
                return text
            
            # Configure anonymization operators
            operators = {}
            for entity_type in entities:
                operators[entity_type] = OperatorConfig(
                    "mask",
                    {
                        "masking_char": settings.pii_mask_char,
                        "chars_to_mask": -1,
                        "from_end": False
                    }
                )
            
            # Anonymize text
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operators
            )
            
            logger.debug(
                "Text anonymized",
                original_length=len(text),
                anonymized_length=len(anonymized_result.text),
                entities_masked=len(analyzer_results)
            )
            
            return anonymized_result.text
            
        except Exception as exc:
            logger.error("Text anonymization failed", error=str(exc))
            # Fallback: return original text
            return text
    
    def extract_pii_data(self, text: str) -> Dict[str, List[str]]:
        """
        Extract specific PII data types from text.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary with extracted PII data by type
        """
        extracted_data = {
            'email': [],
            'phone_number': [],
            'credit_card_number': []
        }
        
        if not text:
            return extracted_data
        
        try:
            # Use Presidio to detect entities
            results = self.analyzer.analyze(
                text=text,
                entities=['EMAIL_ADDRESS', 'PHONE_NUMBER', 'CREDIT_CARD'],
                language='en'
            )
            
            # Extract actual values
            for result in results:
                entity_text = text[result.start:result.end]
                
                if result.entity_type == 'EMAIL_ADDRESS':
                    extracted_data['email'].append(entity_text)
                elif result.entity_type == 'PHONE_NUMBER':
                    extracted_data['phone_number'].append(entity_text)
                elif result.entity_type == 'CREDIT_CARD':
                    extracted_data['credit_card_number'].append(entity_text)
            
            # Remove duplicates
            for key in extracted_data:
                extracted_data[key] = list(set(extracted_data[key]))
            
            logger.debug("PII data extracted", data=extracted_data)
            
            return extracted_data
            
        except Exception as exc:
            logger.error("PII data extraction failed", error=str(exc))
            return extracted_data
    
    def get_entity_statistics(self, text: str) -> Dict[str, int]:
        """
        Get statistics about PII entities in text.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary with entity counts
        """
        if not text:
            return {}
        
        try:
            results = self.analyzer.analyze(
                text=text,
                entities=settings.pii_entities,
                language='en'
            )
            
            stats = {}
            for result in results:
                entity_type = result.entity_type
                stats[entity_type] = stats.get(entity_type, 0) + 1
            
            return stats
            
        except Exception as exc:
            logger.error("Failed to get entity statistics", error=str(exc))
            return {}
