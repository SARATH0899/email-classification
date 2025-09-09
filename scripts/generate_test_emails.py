#!/usr/bin/env python3
"""
Email Generator Script

This script generates 10 test emails of different categories and saves them
as JSON files in the test_data directory, then sends them to the Redis queue.
"""

import sys
import os
import json
import redis
from typing import List, Dict, Any
from pathlib import Path
import structlog

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import EmailInput, EmailCategory
from app.config import settings

logger = structlog.get_logger()


class EmailGenerator:
    """Generator for test emails of different categories."""
    
    def __init__(self):
        """Initialize the email generator."""
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Initialize Redis client
        self.redis_client = redis.from_url(settings.redis_url)
    
    def generate_test_emails(self) -> List[Dict[str, Any]]:
        """Generate 10 test emails of different categories."""
        
        emails = [
            # Marketing Emails
            {
                "from": "marketing@shopify.com",
                "subject": "🚀 Black Friday Sale - 50% Off Everything!",
                "html_content": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        <h1 style="color: #96bf48;">Black Friday Mega Sale!</h1>
                        <p>Dear John Doe,</p>
                        <p>Don't miss our biggest sale of the year! Get 50% off on all products.</p>
                        <p>Your email: john.doe@example.com</p>
                        <p>Phone: +1-555-123-4567</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://shopify.com/sale" style="background: #96bf48; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Shop Now</a>
                        </div>
                        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                            <p>Shopify Inc.</p>
                            <p>150 Elgin Street, Ottawa, ON K2P 1L4, Canada</p>
                            <p><a href="https://shopify.com/unsubscribe">Unsubscribe</a> | <a href="https://shopify.com/privacy">Privacy Policy</a></p>
                        </footer>
                    </div>
                </body>
                </html>
                """,
                "text_content": "Black Friday Mega Sale! Dear John Doe, Don't miss 50% off all products. Email: john.doe@example.com Phone: +1-555-123-4567. Shop at https://shopify.com/sale"
            },
            
            {
                "from": "newsletter@techcrunch.com",
                "subject": "Weekly Tech Digest - AI Breakthroughs",
                "html_content": """
                <html>
                <body>
                    <h2>TechCrunch Weekly Digest</h2>
                    <p>Hi Sarah,</p>
                    <p>Here are this week's top tech stories:</p>
                    <ul>
                        <li>OpenAI releases GPT-5</li>
                        <li>Tesla's new autopilot features</li>
                        <li>Meta's VR advancements</li>
                    </ul>
                    <p>Contact: sarah.tech@gmail.com</p>
                    <footer>
                        <p>TechCrunch, Verizon Media</p>
                        <p>770 Broadway, New York, NY 10003</p>
                        <p><a href="https://techcrunch.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "TechCrunch Weekly Digest. Hi Sarah, Top tech stories: OpenAI GPT-5, Tesla autopilot, Meta VR. Contact: sarah.tech@gmail.com"
            },
            
            # Transactional Emails
            {
                "from": "orders@amazon.com",
                "subject": "Order Confirmation #AMZ-789456123",
                "html_content": """
                <html>
                <body>
                    <h2>Order Confirmation</h2>
                    <p>Dear Michael Johnson,</p>
                    <p>Thank you for your order! Here are the details:</p>
                    <table border="1" style="border-collapse: collapse;">
                        <tr><td>Order Number:</td><td>#AMZ-789456123</td></tr>
                        <tr><td>Total Amount:</td><td>$149.99</td></tr>
                        <tr><td>Payment Method:</td><td>Credit Card ending in 4532</td></tr>
                        <tr><td>Delivery Address:</td><td>123 Main St, Seattle, WA 98101</td></tr>
                    </table>
                    <p>Customer Email: michael.johnson@email.com</p>
                    <p>Phone: (206) 555-0123</p>
                    <footer>
                        <p>Amazon.com, Inc.</p>
                        <p>410 Terry Avenue North, Seattle, WA 98109</p>
                        <p>Customer Service: 1-888-280-4331</p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "Order Confirmation #AMZ-789456123. Dear Michael Johnson, Order total $149.99, Card ending 4532. Email: michael.johnson@email.com Phone: (206) 555-0123"
            },
            
            {
                "from": "billing@stripe.com",
                "subject": "Payment Receipt - Invoice #inv_1234567890",
                "html_content": """
                <html>
                <body>
                    <h2>Payment Receipt</h2>
                    <p>Hello Emma Wilson,</p>
                    <p>Your payment has been successfully processed.</p>
                    <p><strong>Invoice Details:</strong></p>
                    <p>Invoice ID: #inv_1234567890</p>
                    <p>Amount: $99.00</p>
                    <p>Payment Method: Visa ending in 1234</p>
                    <p>Date: November 15, 2024</p>
                    <p>Billing Email: emma.wilson@company.com</p>
                    <p>Phone: +1-415-555-7890</p>
                    <footer>
                        <p>Stripe, Inc.</p>
                        <p>510 Townsend Street, San Francisco, CA 94103</p>
                        <p>Support: support@stripe.com</p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "Payment Receipt #inv_1234567890. Hello Emma Wilson, Payment $99.00 processed. Visa ending 1234. Email: emma.wilson@company.com Phone: +1-415-555-7890"
            },
            
            # Survey Emails
            {
                "from": "feedback@surveymonkey.com",
                "subject": "Quick 2-minute survey - Help us improve!",
                "html_content": """
                <html>
                <body>
                    <h2>We Value Your Feedback</h2>
                    <p>Hi Alex,</p>
                    <p>We hope you enjoyed our service! Please take 2 minutes to share your experience.</p>
                    <p><a href="https://surveymonkey.com/r/feedback123">Take Survey</a></p>
                    <p>Your opinion helps us serve you better.</p>
                    <p>Account: alex.feedback@domain.com</p>
                    <p>Customer ID: CUST-98765</p>
                    <footer>
                        <p>SurveyMonkey Inc.</p>
                        <p>1 Curiosity Way, San Mateo, CA 94403</p>
                        <p><a href="https://surveymonkey.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "We Value Your Feedback. Hi Alex, Please take our 2-minute survey at https://surveymonkey.com/r/feedback123. Account: alex.feedback@domain.com"
            },
            
            {
                "from": "research@typeform.com",
                "subject": "Product Research Survey - $10 Gift Card",
                "html_content": """
                <html>
                <body>
                    <h2>Product Research Survey</h2>
                    <p>Dear Lisa,</p>
                    <p>Participate in our product research and receive a $10 Amazon gift card!</p>
                    <p>Survey takes only 5 minutes to complete.</p>
                    <p><a href="https://typeform.com/survey/product-research">Start Survey</a></p>
                    <p>Participant Email: lisa.research@example.org</p>
                    <p>Reference: REF-2024-1115</p>
                    <footer>
                        <p>Typeform S.L.</p>
                        <p>Carrer de Pujades, 100, 08005 Barcelona, Spain</p>
                        <p>Contact: research@typeform.com</p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "Product Research Survey. Dear Lisa, Complete 5-minute survey for $10 gift card. Email: lisa.research@example.org Ref: REF-2024-1115"
            },
            
            # Personal Emails
            {
                "from": "mom@family.com",
                "subject": "Family Reunion Planning",
                "html_content": """
                <html>
                <body>
                    <h2>Family Reunion 2024</h2>
                    <p>Hi sweetie,</p>
                    <p>I hope you're doing well! I wanted to discuss our family reunion plans.</p>
                    <p>We're thinking of having it at Grandma's house on July 15th.</p>
                    <p>Please let me know if you can make it. Your cousin Jenny will be there too!</p>
                    <p>Call me at (555) 123-4567 when you get a chance.</p>
                    <p>Love,<br>Mom</p>
                    <p>P.S. Don't forget to RSVP to jenny.family@email.com</p>
                </body>
                </html>
                """,
                "text_content": "Family Reunion 2024. Hi sweetie, Planning reunion at Grandma's July 15th. Call me (555) 123-4567. RSVP to jenny.family@email.com. Love, Mom"
            },
            
            {
                "from": "friend@personal.net",
                "subject": "Coffee catch-up this weekend?",
                "html_content": """
                <html>
                <body>
                    <p>Hey there!</p>
                    <p>It's been way too long since we caught up. Want to grab coffee this weekend?</p>
                    <p>I'm free Saturday afternoon or Sunday morning. Let me know what works!</p>
                    <p>My new number is 555-987-6543 in case you need to reach me.</p>
                    <p>Looking forward to hearing from you!</p>
                    <p>Best,<br>Jamie</p>
                    <p>P.S. You can also reach me at jamie.personal@gmail.com</p>
                </body>
                </html>
                """,
                "text_content": "Hey there! Want to grab coffee this weekend? Saturday afternoon or Sunday morning work. New number: 555-987-6543. Email: jamie.personal@gmail.com. Best, Jamie"
            },
            
            # Customer Support Emails
            {
                "from": "support@zendesk.com",
                "subject": "Ticket #ZD-12345 - Account Access Issue Resolved",
                "html_content": """
                <html>
                <body>
                    <h2>Support Ticket Update</h2>
                    <p>Dear Robert Chen,</p>
                    <p>Good news! Your support ticket has been resolved.</p>
                    <p><strong>Ticket Details:</strong></p>
                    <p>Ticket ID: #ZD-12345</p>
                    <p>Issue: Account Access Problem</p>
                    <p>Status: Resolved</p>
                    <p>Resolution: Password reset completed</p>
                    <p>Your account email: robert.chen@business.com</p>
                    <p>Phone on file: +1-650-555-0199</p>
                    <p>If you need further assistance, please reply to this email.</p>
                    <footer>
                        <p>Zendesk Support Team</p>
                        <p>1019 Market Street, San Francisco, CA 94103</p>
                        <p>Support: help@zendesk.com | Phone: 1-888-670-4887</p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "Support Ticket #ZD-12345 Resolved. Dear Robert Chen, Account access issue fixed. Email: robert.chen@business.com Phone: +1-650-555-0199"
            },
            
            {
                "from": "help@slack.com",
                "subject": "Re: Workspace Setup Assistance",
                "html_content": """
                <html>
                <body>
                    <h2>Workspace Setup Complete</h2>
                    <p>Hi Maria,</p>
                    <p>Thank you for contacting Slack support. Your workspace setup is now complete!</p>
                    <p>Here's what we've configured:</p>
                    <ul>
                        <li>Team workspace: "Marketing Team"</li>
                        <li>Admin email: maria.admin@company.co</li>
                        <li>Phone verification: +1-212-555-0147</li>
                        <li>Billing contact: billing@company.co</li>
                    </ul>
                    <p>Your team can now start collaborating!</p>
                    <p>Need more help? Visit our <a href="https://slack.com/help">Help Center</a></p>
                    <footer>
                        <p>Slack Technologies, Inc.</p>
                        <p>500 Howard Street, San Francisco, CA 94105</p>
                        <p>Support: feedback@slack.com</p>
                    </footer>
                </body>
                </html>
                """,
                "text_content": "Workspace Setup Complete. Hi Maria, Marketing Team workspace ready. Admin: maria.admin@company.co Phone: +1-212-555-0147 Billing: billing@company.co"
            }
        ]
        
        return emails
    
    def save_emails_to_files(self, emails: List[Dict[str, Any]]) -> List[Path]:
        """Save emails as JSON files in test_data directory."""
        file_paths = []
        
        for i, email_data in enumerate(emails, 1):
            # Create EmailInput instance for validation
            email_input = EmailInput(**email_data)
            
            # Save as JSON file
            filename = f"email_{i:02d}_{email_input.from_email.split('@')[1].replace('.', '_')}.json"
            file_path = self.test_data_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(email_input.dict(), f, indent=2, ensure_ascii=False)
            
            file_paths.append(file_path)
            logger.info(f"Saved email to {file_path}")
        
        return file_paths
    
    def send_emails_to_queue(self, emails: List[Dict[str, Any]], queue_name: str = "celery") -> int:
        """Send emails to Redis queue for processing."""
        sent_count = 0
        
        for email_data in emails:
            try:
                # Validate email data
                email_input = EmailInput(**email_data)
                
                # Send to Redis queue
                email_json = json.dumps(email_input.dict())
                self.redis_client.lpush(queue_name, email_json)
                
                sent_count += 1
                logger.info(f"Sent email to queue: {email_input.from_email} - {email_input.subject[:50]}")
                
            except Exception as exc:
                logger.error(f"Failed to send email to queue: {exc}")
        
        return sent_count
    
    def run(self):
        """Run the complete email generation and queue process."""
        logger.info("Starting email generation process")
        
        # Generate test emails
        emails = self.generate_test_emails()
        logger.info(f"Generated {len(emails)} test emails")
        
        # Save emails to files
        file_paths = self.save_emails_to_files(emails)
        logger.info(f"Saved {len(file_paths)} email files to {self.test_data_dir}")
        
        # Send emails to queue
        sent_count = self.send_emails_to_queue(emails)
        logger.info(f"Sent {sent_count} emails to Redis queue")
        
        # Print summary
        print(f"\n✅ Email Generation Complete!")
        print(f"📁 Files saved: {len(file_paths)} in {self.test_data_dir}")
        print(f"📤 Queue sent: {sent_count} emails")
        print(f"🔍 Queue length: {self.redis_client.llen('email_processing')}")
        
        return file_paths, sent_count


def main():
    """Main function to run email generation."""
    generator = EmailGenerator()
    generator.run()


if __name__ == "__main__":
    main()
