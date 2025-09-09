"""DynamoDB service for storing processed email results."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import structlog

from app.config import settings
from app.models import ProcessedEmail

logger = structlog.get_logger()


class DynamoDBService:
    """Service for managing DynamoDB operations."""
    
    def __init__(self):
        """Initialize the DynamoDB service."""
        self._initialize_dynamodb()
        self._ensure_table_exists()
    
    def _initialize_dynamodb(self):
        """Initialize DynamoDB client and resource."""
        try:
            # Initialize boto3 session
            session_kwargs = {
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key,
                'region_name': settings.aws_default_region
            }
            
            session = boto3.Session(**session_kwargs)
            
            # Create DynamoDB resource and client with endpoint URL for LocalStack
            resource_kwargs = {}
            client_kwargs = {}
            
            if settings.aws_endpoint_url:
                resource_kwargs['endpoint_url'] = settings.aws_endpoint_url
                client_kwargs['endpoint_url'] = settings.aws_endpoint_url
            
            self.dynamodb = session.resource('dynamodb', **resource_kwargs)
            self.dynamodb_client = session.client('dynamodb', **client_kwargs)
            
            # Get table reference
            self.table = self.dynamodb.Table(settings.dynamodb_table_name)
            
            logger.info("DynamoDB initialized successfully", 
                       table_name=settings.dynamodb_table_name,
                       region=settings.aws_default_region,
                       endpoint_url=settings.aws_endpoint_url)
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as exc:
            logger.error("Failed to initialize DynamoDB", error=str(exc))
            raise
    
    def _ensure_table_exists(self):
        """Ensure the DynamoDB table exists, create if it doesn't."""
        try:
            # Try to describe the table
            self.table.load()
            logger.info("DynamoDB table exists", table_name=settings.dynamodb_table_name)
            
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info("Table not found, creating...", table_name=settings.dynamodb_table_name)
                self._create_table()
            else:
                logger.error("Failed to check table existence", error=str(exc))
                raise
    
    def _create_table(self):
        """Create the DynamoDB table with proper schema."""
        try:
            table = self.dynamodb.create_table(
                TableName=settings.dynamodb_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'sender_domain',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'processed_at',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'sender-domain-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'sender_domain',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'processed_at',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            
            logger.info("DynamoDB table created successfully", 
                       table_name=settings.dynamodb_table_name)
            
        except Exception as exc:
            logger.error("Failed to create DynamoDB table", error=str(exc))
            raise

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        Recursively convert float values to Decimal for DynamoDB compatibility.

        Args:
            obj: Object that may contain float values

        Returns:
            Object with floats converted to Decimals
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        else:
            return obj

    def store_result(self, processed_email: ProcessedEmail) -> str:
        """
        Store processed email result in DynamoDB.
        
        Args:
            processed_email: Processed email result
            
        Returns:
            Document ID of stored result
        """
        try:
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            # Add timestamp
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Prepare item for storage
            item = {
                'id': doc_id,
                'email_category': processed_email.email_category.value,
                'business_entity': self._serialize_business_entity(processed_email.business_entity),
                'data': self._serialize_extracted_data(processed_email.data),
                'confidence_score': processed_email.confidence_score,
                'sender_domain': processed_email.metadata.sender_domain if processed_email.metadata else 'unknown',
                'metadata': self._serialize_metadata(processed_email.metadata),
                'processed_at': timestamp,
                'created_at': timestamp
            }

            # Convert floats to Decimals for DynamoDB compatibility
            item = self._convert_floats_to_decimal(item)

            # Store in DynamoDB
            self.table.put_item(Item=item)
            
            logger.info("Email result stored", doc_id=doc_id, 
                       category=processed_email.email_category.value,
                       confidence=processed_email.confidence_score)
            
            return doc_id
            
        except Exception as exc:
            logger.error("Failed to store email result", error=str(exc))
            raise
    
    def get_result(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve processed email result by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Stored result or None if not found
        """
        try:
            response = self.table.get_item(Key={'id': doc_id})
            
            if 'Item' in response:
                return response['Item']
            else:
                logger.warning("Result not found", doc_id=doc_id)
                return None
                
        except Exception as exc:
            logger.error("Failed to retrieve result", doc_id=doc_id, error=str(exc))
            return None
    
    def query_by_domain(
        self,
        sender_domain: str,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query results by sender domain.
        
        Args:
            sender_domain: Sender domain to query
            limit: Maximum number of results
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            List of matching results
        """
        try:
            # Build query parameters
            query_params = {
                'IndexName': 'sender-domain-index',
                'KeyConditionExpression': 'sender_domain = :domain',
                'ExpressionAttributeValues': {
                    ':domain': sender_domain
                },
                'Limit': limit,
                'ScanIndexForward': False  # Sort by processed_at descending
            }
            
            # Add date range filter if provided
            if start_date or end_date:
                filter_expressions = []
                
                if start_date:
                    filter_expressions.append('processed_at >= :start_date')
                    query_params['ExpressionAttributeValues'][':start_date'] = start_date
                
                if end_date:
                    filter_expressions.append('processed_at <= :end_date')
                    query_params['ExpressionAttributeValues'][':end_date'] = end_date
                
                if filter_expressions:
                    query_params['FilterExpression'] = ' AND '.join(filter_expressions)
            
            # Execute query
            response = self.table.query(**query_params)
            
            results = response.get('Items', [])
            
            logger.debug("Domain query completed", 
                        domain=sender_domain, 
                        count=len(results))
            
            return results
            
        except Exception as exc:
            logger.error("Failed to query by domain", 
                        domain=sender_domain, error=str(exc))
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored results.
        
        Returns:
            Dictionary with statistics
        """
        try:
            # Scan table to get basic statistics
            # Note: This is expensive for large tables, consider using CloudWatch metrics
            response = self.table.scan(
                Select='COUNT'
            )
            
            total_count = response.get('Count', 0)
            
            # Get sample of recent items for category distribution
            sample_response = self.table.scan(
                Limit=100,
                ProjectionExpression='email_category, confidence_score, sender_domain'
            )
            
            items = sample_response.get('Items', [])
            
            # Calculate statistics from sample
            categories = {}
            domains = {}
            confidence_scores = []
            
            for item in items:
                # Category distribution
                category = item.get('email_category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Domain distribution
                domain = item.get('sender_domain', 'unknown')
                domains[domain] = domains.get(domain, 0) + 1
                
                # Confidence scores
                confidence = item.get('confidence_score', 0)
                confidence_scores.append(confidence)
            
            # Calculate average confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            return {
                'total_results': total_count,
                'sample_size': len(items),
                'category_distribution': categories,
                'top_domains': dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]),
                'average_confidence': round(avg_confidence, 3)
            }
            
        except Exception as exc:
            logger.error("Failed to get statistics", error=str(exc))
            return {'total_results': 0, 'error': str(exc)}
    
    def _serialize_business_entity(self, business_entity) -> Dict[str, Any]:
        """Serialize business entity for DynamoDB storage."""
        return {
            'name': business_entity.name,
            'website': str(business_entity.website) if business_entity.website else None,
            'dpo_email': business_entity.dpo_email,
            'industry': business_entity.industry,
            'location': business_entity.location
        }
    
    def _serialize_extracted_data(self, extracted_data) -> Dict[str, Any]:
        """Serialize extracted data for DynamoDB storage."""
        return {
            'email': extracted_data.email or [],
            'phone_number': extracted_data.phone_number or [],
            'credit_card_number': extracted_data.credit_card_number or []
        }
    
    def _serialize_metadata(self, metadata) -> Optional[Dict[str, Any]]:
        """Serialize email metadata for DynamoDB storage."""
        if not metadata:
            return None
        
        return {
            'sender_domain': metadata.sender_domain,
            'footer_text': metadata.footer_text,
            'urls': metadata.urls
        }
