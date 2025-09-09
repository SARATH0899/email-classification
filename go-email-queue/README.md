# Go Email Queue Manager

A Go service that reads email files from the `test_data` directory and adds them to the Celery queue for processing using the official gocelery client.

## Features

- **File-based Email Processing**: Reads JSON email files from test_data directory
- **Official Celery Integration**: Uses gocelery client for guaranteed compatibility
- **Redis Queue Management**: Uses Redis as the message broker
- **Email Validation**: Validates email files before queuing
- **Comprehensive Logging**: Detailed logging with progress tracking
- **Error Handling**: Graceful error handling with detailed reporting
- **Native Celery Format**: Creates properly formatted Celery messages

## Configuration

The service uses environment variables for configuration:

- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `CELERY_QUEUE_NAME`: Celery queue name (default: `celery`)
- `TEST_DATA_DIR`: Directory containing email files (default: `/app/test_data`)

## Email File Format

Each email file should be a JSON file with the following structure:

```json
{
  "from": "sender@example.com",
  "subject": "Email Subject",
  "html_content": "<html><body>Email content</body></html>"
}
```

## Usage

### Docker Compose

The service is configured to run as part of the Docker Compose stack:

```bash
# Build and run the service
docker-compose up go-email-queue

# Run as one-time job
docker-compose run --rm go-email-queue
```

### Standalone

```bash
# Build the binary
go build -o email-queue-manager main.go

# Run with default configuration
./email-queue-manager

# Run with custom configuration
REDIS_URL=redis://localhost:6379/1 \
CELERY_QUEUE_NAME=email_processing \
TEST_DATA_DIR=./emails \
./email-queue-manager
```

## How It Works

1. **Scan Directory**: Scans the test_data directory for JSON email files
2. **Validate Files**: Validates each email file has required fields
3. **Create Celery Tasks**: Creates properly formatted Celery task messages
4. **Queue Tasks**: Adds tasks to Redis queue for Celery workers to process
5. **Monitor Progress**: Provides detailed progress reporting and statistics

## Task Format

The service creates Celery tasks with the following structure:

```json
{
  "id": "unique-task-id",
  "task": "app.tasks.process_email_task",
  "args": ["email_filename.json"],
  "kwargs": {},
  "retries": 0,
  "eta": null,
  "expires": null,
  "utc": true
}
```

## Dependencies

- `github.com/gocelery/gocelery`: Official Go client for Celery
- `github.com/gomodule/redigo`: Redis client for Go (used by gocelery)
- `github.com/google/uuid`: UUID generation for task IDs

## Monitoring

- **Redis Commander**: Available at http://localhost:8081
- **Flower (Celery)**: Available at http://localhost:5555
- **Logs**: Detailed logging with structured output

## Error Handling

The service handles various error conditions:

- **File Not Found**: Skips missing files with error logging
- **Invalid JSON**: Reports JSON parsing errors
- **Missing Fields**: Validates required email fields
- **Redis Connection**: Handles Redis connection failures
- **Queue Errors**: Reports queuing failures with details

## Performance

- **Batch Processing**: Processes all email files in sequence
- **Rate Limiting**: Small delays between tasks to avoid overwhelming the queue
- **Memory Efficient**: Processes files one at a time
- **Connection Pooling**: Uses Redis connection pooling for efficiency
