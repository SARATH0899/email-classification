"""Test configuration and fixtures."""

import pytest
import os
from unittest.mock import Mock, patch
from app.models import EmailInput, EmailMetadata, BusinessEntity, EmailCategory


@pytest.fixture
def sample_email_input():
    """Sample email input for testing."""
    return EmailInput(
        from_email="marketing@example.com",
        subject="Welcome to our service!",
        html_content="""
        <html>
        <body>
            <h1>Welcome!</h1>
            <p>Thank you for joining our service.</p>
            <footer>
                <p>Company Inc.</p>
                <p>123 Main St, City, State</p>
                <p><a href="https://example.com/unsubscribe">Unsubscribe</a></p>
            </footer>
        </body>
        </html>
        """,
        text_content="Welcome! Thank you for joining our service. Company Inc. 123 Main St, City, State"
    )


@pytest.fixture
def sample_metadata():
    """Sample email metadata for testing."""
    return EmailMetadata(
        sender_domain="example.com",
        footer_text="Company Inc.\n123 Main St, City, State\nUnsubscribe",
        urls=["https://example.com/unsubscribe"]
    )


@pytest.fixture
def sample_business_entity():
    """Sample business entity for testing."""
    return BusinessEntity(
        name="Example Company",
        website="https://example.com",
        dpo_email="dpo@example.com",
        industry="Technology",
        location="San Francisco, CA"
    )


@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API responses."""
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_create.return_value = {
            'choices': [{
                'message': {
                    'content': '{"email_category": "marketing", "business_entity": {"name": "Test Company"}, "data": {}, "confidence_score": 0.9}'
                }
            }]
        }
        yield mock_create


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('redis.from_url') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB service."""
    with patch('boto3.Session') as mock_session:
        mock_table = Mock()
        mock_session.return_value.resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client."""
    with patch('chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        yield mock_collection


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    test_env = {
        'OPENAI_API_KEY': 'test-key',
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
        'REDIS_URL': 'redis://localhost:6379/1',
        'DYNAMODB_TABLE_NAME': 'test-email-results',
        'CHROMA_PERSIST_DIRECTORY': './test_data/chroma'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield
    
    # Cleanup
    for key in test_env.keys():
        if key in os.environ:
            del os.environ[key]
