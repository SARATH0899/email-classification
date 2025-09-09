"""Celery tasks for email processing."""

import json
import os
import structlog
from pathlib import Path
from typing import Dict, Any
from celery import Task
from app.celery_app import celery_app
from app.models import EmailInput, ProcessedEmail
from app.services.email_processor import EmailProcessor
from app.database.dynamodb import DynamoDBService

logger = structlog.get_logger()


def load_email_from_file(email_filename: str) -> Dict[str, Any]:
    """
    Load email data from a JSON file in the test_data directory.

    Args:
        email_filename: Name of the email file (e.g., 'email_01_marketing_shopify_com.json')

    Returns:
        Dictionary containing email data

    Raises:
        FileNotFoundError: If the email file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the email data is missing required fields
    """
    # Get test data directory path
    test_data_dir = os.environ.get('TEST_DATA_DIR', '/app/test_data')
    file_path = Path(test_data_dir) / email_filename

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"Email file not found: {file_path}")

    # Load and parse JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            email_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {email_filename}: {e}")

    # Validate required fields
    required_fields = ['from', 'subject', 'html_content']
    missing_fields = [field for field in required_fields if field not in email_data]
    if missing_fields:
        raise ValueError(f"Missing required fields in {email_filename}: {missing_fields}")

    logger.info("Email loaded from file", filename=email_filename, fields=list(email_data.keys()))
    return email_data


class CallbackTask(Task):
    """Base task class with callbacks."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success."""
        logger.info("Task completed successfully", task_id=task_id)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        logger.error("Task failed", task_id=task_id, error=str(exc))


@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.process_email_task")
def process_email_task(self, email_filename: str) -> Dict[str, Any]:
    """
    Process a single email through the complete pipeline.

    Args:
        email_filename: Name of the email file in test_data directory

    Returns:
        Processed email result dictionary
    """
    try:
        logger.info("Starting email processing",
                   task_id=self.request.id,
                   email_file=email_filename)

        # Load email data from file
        email_data = load_email_from_file(email_filename)

        # Validate input
        email_input = EmailInput(**email_data)

        # Initialize services
        processor = EmailProcessor()
        db_service = DynamoDBService()

        # Process the email
        result = processor.process_email(email_input)

        # Store result in DynamoDB
        doc_id = db_service.store_result(result)

        logger.info(
            "Email processing completed",
            task_id=self.request.id,
            email_file=email_filename,
            doc_id=doc_id,
            category=result.email_category,
            confidence=result.confidence_score
        )

        # Return detailed result
        return {
            "task_id": self.request.id,
            "email_filename": email_filename,
            "doc_id": doc_id,
            "email_category": result.email_category.value,
            "business_entity": {
                "name": result.business_entity.name,
                "website": str(result.business_entity.website) if result.business_entity.website else None,
                "industry": result.business_entity.industry,
                "location": result.business_entity.location,
                "dpo_email": result.business_entity.dpo_email
            },
            "confidence_score": result.confidence_score,
            "processed_at": result.processed_at,
            "sender_domain": result.metadata.sender_domain if result.metadata else None
        }

    except Exception as exc:
        logger.error(
            "Email processing failed",
            task_id=self.request.id,
            email_file=email_filename,
            error=str(exc),
            exc_info=True
        )
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(name="batch_process_emails")
def batch_process_emails_task(email_filenames: list) -> Dict[str, Any]:
    """
    Process a batch of emails.

    Args:
        email_filenames: List of email filenames

    Returns:
        Batch processing results
    """
    results = []
    errors = []

    for i, email_filename in enumerate(email_filenames):
        try:
            # Process each email asynchronously
            task_result = process_email_task.delay(email_filename)
            results.append({
                "index": i,
                "email_filename": email_filename,
                "task_id": task_result.id,
                "status": "queued"
            })
        except Exception as exc:
            errors.append({
                "index": i,
                "email_filename": email_filename,
                "error": str(exc)
            })

    return {
        "total": len(email_filenames),
        "queued": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors
    }
