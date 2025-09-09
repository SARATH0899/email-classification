package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gocelery/gocelery"
	"github.com/gomodule/redigo/redis"
)

// EmailQueueManager handles email queue operations using gocelery
type EmailQueueManager struct {
	celeryClient *gocelery.CeleryClient
	queueName    string
}

// NewEmailQueueManager creates a new email queue manager using gocelery
func NewEmailQueueManager(redisURL, queueName string) *EmailQueueManager {
	// Create Redis connection pool
	redisPool := &redis.Pool{
		MaxIdle:     3,
		IdleTimeout: 240 * time.Second,
		Dial: func() (redis.Conn, error) {
			return redis.DialURL(redisURL)
		},
	}

	// Create Redis broker for gocelery
	redisBroker := gocelery.NewRedisBroker(redisPool)

	// Create Redis backend for gocelery
	redisBackend := gocelery.NewRedisCeleryBackend(redisURL)

	// Create Celery client
	celeryClient, err := gocelery.NewCeleryClient(redisBroker, redisBackend, 1)
	if err != nil {
		log.Fatalf("Failed to create Celery client: %v", err)
	}

	return &EmailQueueManager{
		celeryClient: celeryClient,
		queueName:    queueName,
	}
}

// Close closes the Celery client
func (eq *EmailQueueManager) Close() {
	// gocelery client doesn't need explicit closing
	log.Println("📋 Celery client closed")
}

// AddEmailToQueue adds an email filename to the Celery queue using gocelery
func (eq *EmailQueueManager) AddEmailToQueue(emailFilename string) error {
	// Create task arguments
	args := []interface{}{emailFilename}

	// Submit task using gocelery client
	asyncResult, err := eq.celeryClient.Delay("app.tasks.process_email_task", args...)
	if err != nil {
		return fmt.Errorf("failed to submit task: %v", err)
	}

	log.Printf("✅ Added email '%s' to queue with task ID: %s", emailFilename, asyncResult.TaskID)
	return nil
}

// GetEmailFiles returns all JSON email files from the test_data directory
func GetEmailFiles(testDataDir string) ([]string, error) {
	var emailFiles []string

	err := filepath.Walk(testDataDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".json") {
			// Only include email files (not summary files)
			if strings.HasPrefix(info.Name(), "email_") {
				emailFiles = append(emailFiles, info.Name())
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to read test_data directory: %v", err)
	}

	return emailFiles, nil
}

// ValidateEmailFile validates that an email file has the required structure
func ValidateEmailFile(filePath string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read file: %v", err)
	}

	var email map[string]interface{}
	if err := json.Unmarshal(data, &email); err != nil {
		return fmt.Errorf("invalid JSON: %v", err)
	}

	// Check required fields
	requiredFields := []string{"from", "subject", "html_content"}
	for _, field := range requiredFields {
		if _, exists := email[field]; !exists {
			return fmt.Errorf("missing required field: %s", field)
		}
	}

	return nil
}

func main() {
	log.Println("🚀 Starting Go Email Queue Manager")
	log.Println("=" + strings.Repeat("=", 40))

	// Configuration
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://localhost:6379/0"
	}

	queueName := os.Getenv("CELERY_QUEUE_NAME")
	if queueName == "" {
		queueName = "celery"
	}

	testDataDir := os.Getenv("TEST_DATA_DIR")
	if testDataDir == "" {
		testDataDir = "/app/test_data"
	}

	log.Printf("📋 Configuration:")
	log.Printf("  Redis URL: %s", redisURL)
	log.Printf("  Queue Name: %s", queueName)
	log.Printf("  Test Data Dir: %s", testDataDir)

	// Initialize queue manager
	queueManager := NewEmailQueueManager(redisURL, queueName)
	defer queueManager.Close()

	log.Println("✅ Celery client initialized successfully")

	// Get email files
	emailFiles, err := GetEmailFiles(testDataDir)
	if err != nil {
		log.Fatalf("❌ Failed to get email files: %v", err)
	}

	if len(emailFiles) == 0 {
		log.Fatalf("❌ No email files found in %s", testDataDir)
	}

	log.Printf("📧 Found %d email files", len(emailFiles))

	// Validate and queue emails
	successCount := 0
	errorCount := 0

	for i, emailFile := range emailFiles {
		log.Printf("\n📧 Processing email %d/%d: %s", i+1, len(emailFiles), emailFile)

		// Validate email file
		filePath := filepath.Join(testDataDir, emailFile)
		if err := ValidateEmailFile(filePath); err != nil {
			log.Printf("❌ Validation failed for %s: %v", emailFile, err)
			errorCount++
			continue
		}

		// Add to queue
		if err := queueManager.AddEmailToQueue(emailFile); err != nil {
			log.Printf("❌ Failed to queue %s: %v", emailFile, err)
			errorCount++
			continue
		}

		successCount++

		// Small delay to avoid overwhelming the queue
		time.Sleep(100 * time.Millisecond)
	}

	// Summary
	log.Println("\n📊 Processing Summary")
	log.Println("=" + strings.Repeat("=", 30))
	log.Printf("✅ Successfully queued: %d emails", successCount)
	log.Printf("❌ Failed: %d emails", errorCount)
	log.Printf("📈 Success rate: %.1f%%", float64(successCount)/float64(len(emailFiles))*100)

	if successCount > 0 {
		log.Println("\n🎉 Email queue processing completed successfully!")
		log.Printf("💡 Monitor queue status at: http://localhost:8081 (Redis Commander)")
		log.Printf("🌸 Monitor Celery tasks at: http://localhost:5555 (Flower)")
	} else {
		log.Println("\n❌ No emails were successfully queued")
		os.Exit(1)
	}
}
