.PHONY: help build up down logs test clean demo install-dev lint format

# Default target
help:
	@echo "Email Processing Application - Available Commands:"
	@echo ""
	@echo "  build        Build Docker images"
	@echo "  up           Start all services"
	@echo "  down         Stop all services"
	@echo "  logs         View application logs"
	@echo "  test         Run tests"
	@echo "  test-imports Test all imports"
	@echo "  test-llm     Run LLM evaluation tests"
	@echo "  test-providers Test different LLM providers"
	@echo "  test-queue   Test Celery queue format"
	@echo "  debug-queue  Debug real Celery message format"
	@echo "  test-pii     Test PII detection configuration"
	@echo "  test-privacy Test privacy policy scraper"
	@echo "  test-dynamodb Test DynamoDB decimal conversion"
	@echo "  test-chromadb Test ChromaDB configuration"
	@echo "  health-check Run comprehensive health check"
	@echo "  queue-emails Queue emails using Go service"
	@echo "  demo         Run email processing demo"
	@echo "  generate-emails Generate test emails"
	@echo "  clean        Clean up containers and volumes"
	@echo "  install-dev  Install development dependencies"
	@echo "  lint         Run code linting"
	@echo "  format       Format code"
	@echo ""

# Docker commands
build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  - Flower: http://localhost:5555"
	@echo "  - LocalStack: http://localhost:4566"

down:
	@echo "Stopping services..."
	docker-compose down

logs:
	@echo "Viewing logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Development commands
install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm
	playwright install chromium

test:
	@echo "Running tests..."
	pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	@echo "Running linting..."
	flake8 app/ tests/ scripts/
	mypy app/

format:
	@echo "Formatting code..."
	black app/ tests/ scripts/

# Demo and utilities
demo:
	@echo "Running email processing demo..."
	python scripts/startup.py run-processing

generate-emails:
	@echo "Generating test emails..."
	python scripts/startup.py generate-emails

test-imports:
	@echo "Testing imports..."
	python scripts/startup.py test-imports

test-llm:
	@echo "Running LLM evaluation tests..."
	pytest tests/test_llm_evaluation.py -v

test-providers:
	@echo "Testing different LLM providers..."
	python scripts/startup.py test-providers

health-check:
	@echo "Running health check..."
	python scripts/startup.py health-check

test-queue:
	@echo "Testing Celery queue format..."
	python scripts/startup.py test-queue

debug-queue:
	@echo "Debugging Celery queue format..."
	python scripts/startup.py debug-queue

test-pii:
	@echo "Testing PII configuration..."
	python scripts/startup.py test-pii

test-privacy:
	@echo "Testing privacy policy scraper..."
	python scripts/startup.py test-privacy

test-dynamodb:
	@echo "Testing DynamoDB decimal conversion..."
	python scripts/startup.py test-dynamodb

test-chromadb:
	@echo "Testing ChromaDB configuration..."
	python scripts/test_chromadb_config.py

queue-emails:
	@echo "Queuing emails with Go service..."
	docker-compose run --rm go-email-queue

# Cleanup commands
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	docker system prune -f

clean-all:
	@echo "Cleaning up everything (including images)..."
	docker-compose down -v --rmi all
	docker system prune -af

# Database commands
create-dynamodb-table:
	@echo "Creating DynamoDB table locally..."
	aws dynamodb create-table \
		--table-name email_processing_results \
		--attribute-definitions \
			AttributeName=id,AttributeType=S \
			AttributeName=sender_domain,AttributeType=S \
			AttributeName=processed_at,AttributeType=S \
		--key-schema \
			AttributeName=id,KeyType=HASH \
		--global-secondary-indexes \
			IndexName=sender-domain-index,KeySchema=[{AttributeName=sender_domain,KeyType=HASH},{AttributeName=processed_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
		--provisioned-throughput \
			ReadCapacityUnits=5,WriteCapacityUnits=5 \
		--endpoint-url http://localhost:8000

# Development server commands
dev-server:
	@echo "Starting development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	@echo "Starting development Celery worker..."
	celery -A app.celery_app worker --loglevel=info --reload

dev-flower:
	@echo "Starting Celery Flower..."
	celery -A app.celery_app flower

# Monitoring commands
status:
	@echo "Service status:"
	docker-compose ps

health:
	@echo "Checking services health..."
	@echo "LocalStack:"
	@curl -f http://localhost:4566/health 2>/dev/null && echo "  ✅ LocalStack OK" || echo "  ❌ LocalStack not responding"
	@echo "Application:"
	@make health-check

# Setup commands
setup: build up
	@echo "Waiting for services to start..."
	sleep 10
	@echo "Running health check..."
	make health
	@echo "Setup complete!"

# Quick start for new developers
quickstart:
	@echo "Quick start for new developers..."
	@echo "1. Copying environment file..."
	cp .env.example .env
	@echo "2. Please edit .env file with your API keys"
	@echo "3. Run 'make setup' to build and start services"
	@echo "4. Run 'make demo' to test the application"
