# Email Processing Application

A modular, containerized Python application for processing emails with PII masking, similarity matching, and business entity classification using LLMs. Features LocalStack for local DynamoDB development and Deepeval for LLM quality testing.

## Features

- **Email Ingestion**: Celery workers process emails from Redis queue
- **HTML Stripping**: Clean HTML content using BeautifulSoup
- **PII Anonymization**: Mask personally identifiable information using SpaCy and Microsoft Presidio
- **Metadata Extraction**: Extract sender domain, footer text, and URLs
- **Vector Similarity Search**: ChromaDB-based similarity matching with confidence scoring
- **LLM Classification**: Fallback classification using OpenAI GPT models
- **Business Entity Extraction**: Extract company information and DPO emails
- **Privacy Policy Scraping**: Automated DPO email extraction from privacy policies
- **DynamoDB Storage**: Store processed results with proper indexing

## Architecture

```
app/
├── database/           # Database operations
│   ├── dynamodb.py    # DynamoDB service
│   └── vector_store.py # ChromaDB operations
├── llm/               # LLM components
│   ├── models.py      # Model management
│   └── chains.py      # LangChain chains
├── processing/        # Content processing
│   ├── html_processor.py
│   └── pii_processor.py
└── services/          # Core services
    ├── email_processor.py
    ├── metadata_extractor.py
    └── similarity_matcher.py
```

### Processing Pipeline
```
Email Input → HTML Stripping → PII Masking → Metadata Extraction
     ↓
Vector Search → Confidence Check → LLM Classification (if needed)
     ↓
Business Entity Enhancement → DynamoDB Storage → Vector DB Update
```

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd email-processing-app
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Run Email Processing**:
   ```bash
   # Generate test emails and process them
   make demo

   # Or generate emails only
   make generate-emails

   # Run LLM evaluation tests
   make test-llm
   ```

## Configuration

### Environment Variables

#### LLM Configuration
- `LLM_PROVIDER`: LLM provider to use (`openai`, `gemini`, `ollama`)
- `LLM_TEMPERATURE`: Temperature for LLM responses (default: 0.1)
- `LLM_MAX_TOKENS`: Maximum tokens for LLM responses (default: 1000)

#### Provider-Specific Settings
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL`: OpenAI model name (default: gpt-3.5-turbo)
- `GEMINI_API_KEY`: Google Gemini API key
- `GEMINI_MODEL`: Gemini model name (default: gemini-pro)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: llama2)

#### Other Configuration
- `AWS_ACCESS_KEY_ID`: AWS access key for DynamoDB
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for DynamoDB
- `REDIS_URL`: Redis connection URL
- `DYNAMODB_TABLE_NAME`: DynamoDB table name
- `CONFIDENCE_THRESHOLD`: Confidence threshold for vector matching (default: 0.85)

### Services

- **LocalStack**: Local AWS services (DynamoDB) on port 4566
- **Celery Worker**: Background email processing
- **Celery Flower**: Task monitoring on port 5555
- **Redis**: Message broker and result backend
- **ChromaDB**: Vector database for similarity search

## Scripts and Commands

### Generate Test Emails
```bash
python scripts/generate_test_emails.py
```
Generates 10 test emails of different categories and saves them to `test_data/` directory.

### Run Complete Processing Pipeline
```bash
python scripts/run_email_processing.py
```
Processes all test emails through the complete pipeline and displays results.

### Run LLM Evaluation Tests
```bash
pytest tests/test_llm_evaluation.py -v
```
Evaluates LLM output quality using Deepeval metrics.

### Test Different LLM Providers
```bash
python scripts/test_llm_providers.py
```
Tests and compares OpenAI, Gemini, and Ollama providers for email classification.

## Processing Pipeline

1. **HTML Stripping**: Extract clean text from HTML content
2. **PII Anonymization**: Mask sensitive information using Presidio
3. **Metadata Extraction**: Extract domain, URLs, and footer information
4. **Vector Search**: Find similar emails in ChromaDB
5. **Confidence Scoring**: Calculate confidence based on similarity and domain matching
6. **Classification**: Use vector match or LLM fallback for classification
7. **Business Entity Extraction**: Extract company information
8. **DPO Email Scraping**: Scrape privacy policies for DPO emails if needed
9. **Storage**: Store results in DynamoDB and update vector database

## Email Categories

- `marketing`: Promotional content, newsletters
- `transactional`: Order confirmations, receipts
- `survey`: Feedback requests, questionnaires
- `personal`: Personal communications
- `customer_support`: Help desk responses, support tickets


## Monitoring and Testing

- **Celery Flower**: http://localhost:5555 (Task monitoring)
- **LocalStack**: http://localhost:4566 (Local AWS services)
- **DynamoDB Admin**: http://localhost:8001/
- **ChromaDB Admin**: http://localhost:3001/
- **Redis Commander**: http://localhost:8081
- **Deepeval**: LLM output quality evaluation
- **Logs**: Check Docker logs or application logs

### Multi-Provider LLM Support
The application supports multiple LLM providers:
- **OpenAI**: GPT-3.5-turbo, GPT-4 models
- **Google Gemini**: Gemini-pro model
- **Ollama**: Local LLM deployment (Llama2, Mistral, etc.)

Switch providers by setting the `LLM_PROVIDER` environment variable.

### Separated Prompts Architecture
Prompts are separated from logic in the `app/prompts/` directory:
- `email_classification.py`: Email classification prompts
- `dpo_extraction.py`: DPO email extraction prompts

This allows for easy prompt engineering and A/B testing.

### LLM Quality Testing
The application includes comprehensive LLM evaluation using Deepeval:
- **Answer Relevancy**: Tests if classifications are relevant to email content
- **Faithfulness**: Ensures outputs are faithful to input content
- **Contextual Precision**: Measures classification accuracy
- **Model Comparison**: Compares different LLM models and providers
- **Token Usage Efficiency**: Monitors response times and resource usage

## Scaling

- Scale Celery workers: `docker-compose up --scale celery-worker=3`
- Configure Redis clustering for high availability
- Use DynamoDB auto-scaling for storage
- Deploy ChromaDB with persistent storage

## Security

- PII data is anonymized before storage
- API keys are managed through environment variables
- Network isolation through Docker containers
- HTTPS recommended for production deployment
