#!/usr/bin/env python3
"""
Generate 20 Test Emails Script

This script generates 20 test emails across different categories and saves them
as separate JSON files in the test_data directory.
"""

import sys
import os
import json
from typing import List, Dict, Any
from pathlib import Path
import structlog

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import EmailInput

logger = structlog.get_logger()


class EmailGenerator20:
    """Generator for 20 test emails across all categories."""
    
    def __init__(self):
        """Initialize the email generator."""
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
    
    def generate_emails(self) -> List[Dict[str, Any]]:
        """Generate 20 test emails across all categories."""
        
        emails = []
        
        # Marketing Emails (4 emails)
        marketing_emails = [
            {
                "from": "marketing@shopify.com",
                "subject": "🚀 Black Friday Sale - 50% Off Everything!",
                "html_content": """<html><body>
                    <h1>Black Friday Mega Sale!</h1>
                    <p>Dear Customer,</p>
                    <p>Don't miss our biggest sale of the year! Get 50% off on all products.</p>
                    <p>Contact: customer@example.com | Phone: +1-555-123-4567</p>
                    <a href="https://shopify.com/sale">Shop Now</a>
                    <footer>
                        <p>Shopify Inc. | 150 Elgin Street, Ottawa, ON</p>
                        <p><a href="https://shopify.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "newsletter@techcrunch.com",
                "subject": "Weekly Tech Digest - AI Breakthroughs",
                "html_content": """<html><body>
                    <h2>TechCrunch Weekly Digest</h2>
                    <p>Hi Tech Enthusiast,</p>
                    <p>Here are this week's top tech stories:</p>
                    <ul>
                        <li>OpenAI releases GPT-5</li>
                        <li>Tesla's new autopilot features</li>
                        <li>Meta's VR advancements</li>
                    </ul>
                    <p>Contact: sarah.tech@gmail.com</p>
                    <footer>
                        <p>TechCrunch, Verizon Media</p>
                        <p><a href="https://techcrunch.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "deals@amazon.com",
                "subject": "Prime Day Exclusive - Up to 70% Off Electronics",
                "html_content": """<html><body>
                    <h1>Prime Day is Here!</h1>
                    <p>Hello Prime Member,</p>
                    <p>Exclusive deals just for you! Save up to 70% on electronics.</p>
                    <p>Member email: prime.member@email.com</p>
                    <p>Member phone: (206) 266-1000</p>
                    <a href="https://amazon.com/primeday">Shop Prime Deals</a>
                    <footer>
                        <p>Amazon.com, Inc.</p>
                        <p><a href="https://amazon.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "promo@netflix.com",
                "subject": "New Movies & Shows This Week",
                "html_content": """<html><body>
                    <h2>What's New on Netflix</h2>
                    <p>Hi Movie Lover,</p>
                    <p>Check out the latest additions to Netflix this week!</p>
                    <p>Account: movie.lover@streaming.com</p>
                    <a href="https://netflix.com/browse">Watch Now</a>
                    <footer>
                        <p>Netflix, Inc.</p>
                        <p><a href="https://netflix.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body></html>"""
            }
        ]
        
        # Transactional Emails (4 emails)
        transactional_emails = [
            {
                "from": "orders@amazon.com",
                "subject": "Order Confirmation #AMZ-789456123",
                "html_content": """<html><body>
                    <h2>Order Confirmation</h2>
                    <p>Dear Michael Johnson,</p>
                    <p>Thank you for your order!</p>
                    <table>
                        <tr><td>Order Number:</td><td>#AMZ-789456123</td></tr>
                        <tr><td>Total Amount:</td><td>$149.99</td></tr>
                        <tr><td>Payment Method:</td><td>Credit Card ending in 4532</td></tr>
                    </table>
                    <p>Customer Email: michael.johnson@email.com</p>
                    <p>Phone: (206) 555-0123</p>
                    <footer>
                        <p>Amazon.com, Inc.</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "billing@stripe.com",
                "subject": "Payment Receipt - Invoice #inv_1234567890",
                "html_content": """<html><body>
                    <h2>Payment Receipt</h2>
                    <p>Hello Emma Wilson,</p>
                    <p>Your payment has been successfully processed.</p>
                    <p>Invoice ID: #inv_1234567890</p>
                    <p>Amount: $99.00</p>
                    <p>Payment Method: Visa ending in 1234</p>
                    <p>Billing Email: emma.wilson@company.com</p>
                    <p>Phone: +1-415-555-7890</p>
                    <footer>
                        <p>Stripe, Inc.</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "noreply@paypal.com",
                "subject": "You've received a payment of $250.00",
                "html_content": """<html><body>
                    <h2>Payment Received</h2>
                    <p>Hi Sarah,</p>
                    <p>You've received a payment of $250.00 from John Smith.</p>
                    <p>Transaction ID: 1AB23456CD789012E</p>
                    <p>Your PayPal email: sarah.payments@business.com</p>
                    <p>Contact: +1-888-221-1161</p>
                    <footer>
                        <p>PayPal, Inc.</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "receipts@uber.com",
                "subject": "Your trip receipt for $18.45",
                "html_content": """<html><body>
                    <h2>Trip Receipt</h2>
                    <p>Hi Alex,</p>
                    <p>Thanks for riding with Uber!</p>
                    <p>Trip fare: $18.45</p>
                    <p>Payment method: Card ending in 9876</p>
                    <p>Account: alex.rider@email.com</p>
                    <p>Phone: +1-555-987-6543</p>
                    <footer>
                        <p>Uber Technologies, Inc.</p>
                    </footer>
                </body></html>"""
            }
        ]
        
        # Survey Emails (4 emails)
        survey_emails = [
            {
                "from": "feedback@surveymonkey.com",
                "subject": "Quick 2-minute survey - Help us improve!",
                "html_content": """<html><body>
                    <h2>We Value Your Feedback</h2>
                    <p>Hi Alex,</p>
                    <p>Please take 2 minutes to share your experience.</p>
                    <a href="https://surveymonkey.com/r/feedback123">Take Survey</a>
                    <p>Account: alex.feedback@domain.com</p>
                    <p>Customer ID: CUST-98765</p>
                    <footer>
                        <p>SurveyMonkey Inc.</p>
                        <p><a href="https://surveymonkey.com/unsubscribe">Unsubscribe</a></p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "research@typeform.com",
                "subject": "Product Research Survey - $10 Gift Card",
                "html_content": """<html><body>
                    <h2>Product Research Survey</h2>
                    <p>Dear Lisa,</p>
                    <p>Participate in our research and receive a $10 Amazon gift card!</p>
                    <a href="https://typeform.com/survey/product-research">Start Survey</a>
                    <p>Participant Email: lisa.research@example.org</p>
                    <p>Reference: REF-2024-1115</p>
                    <footer>
                        <p>Typeform S.L.</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "surveys@google.com",
                "subject": "Google Opinion Rewards - Earn Credits",
                "html_content": """<html><body>
                    <h2>New Survey Available</h2>
                    <p>Hello Survey Participant,</p>
                    <p>A new survey is available. Complete it to earn Google Play credits!</p>
                    <p>Estimated time: 1-2 minutes</p>
                    <p>Account: survey.user@gmail.com</p>
                    <a href="https://surveys.google.com/start">Start Survey</a>
                    <footer>
                        <p>Google LLC</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "feedback@airbnb.com",
                "subject": "How was your stay? Leave a review",
                "html_content": """<html><body>
                    <h2>Rate Your Recent Stay</h2>
                    <p>Hi Travel Guest,</p>
                    <p>How was your recent stay in San Francisco?</p>
                    <p>Your feedback helps other travelers.</p>
                    <p>Guest email: travel.guest@vacation.com</p>
                    <a href="https://airbnb.com/review/12345">Leave Review</a>
                    <footer>
                        <p>Airbnb, Inc.</p>
                    </footer>
                </body></html>"""
            }
        ]
        
        # Personal Emails (4 emails)
        personal_emails = [
            {
                "from": "mom@family.com",
                "subject": "Family Reunion Planning",
                "html_content": """<html><body>
                    <h2>Family Reunion 2024</h2>
                    <p>Hi sweetie,</p>
                    <p>I hope you're doing well! Planning our family reunion for July 15th.</p>
                    <p>Please let me know if you can make it.</p>
                    <p>Call me at (555) 123-4567 when you get a chance.</p>
                    <p>Love, Mom</p>
                    <p>P.S. RSVP to jenny.family@email.com</p>
                </body></html>"""
            },
            {
                "from": "friend@personal.net",
                "subject": "Coffee catch-up this weekend?",
                "html_content": """<html><body>
                    <p>Hey there!</p>
                    <p>It's been way too long since we caught up. Want to grab coffee this weekend?</p>
                    <p>I'm free Saturday afternoon or Sunday morning.</p>
                    <p>My new number is 555-987-6543.</p>
                    <p>Looking forward to hearing from you!</p>
                    <p>Best, Jamie</p>
                    <p>P.S. You can also reach me at jamie.personal@gmail.com</p>
                </body></html>"""
            },
            {
                "from": "college.buddy@alumni.edu",
                "subject": "Class of 2015 Reunion - Save the Date!",
                "html_content": """<html><body>
                    <h2>Class of 2015 Reunion</h2>
                    <p>Hey Classmate,</p>
                    <p>Can you believe it's been 9 years since graduation?</p>
                    <p>We're planning our reunion for next summer!</p>
                    <p>Contact me at reunion.planner@alumni.edu</p>
                    <p>Phone: (555) 234-5678</p>
                    <p>Best regards,<br>Your Reunion Committee</p>
                </body></html>"""
            },
            {
                "from": "neighbor@community.org",
                "subject": "Neighborhood BBQ This Saturday",
                "html_content": """<html><body>
                    <h2>Community BBQ</h2>
                    <p>Hi Neighbor,</p>
                    <p>You're invited to our annual neighborhood BBQ this Saturday at 2 PM!</p>
                    <p>Location: Community Park</p>
                    <p>Please bring a side dish to share.</p>
                    <p>RSVP: community.organizer@neighborhood.org</p>
                    <p>Questions? Call (555) 345-6789</p>
                    <p>See you there!</p>
                </body></html>"""
            }
        ]
        
        # Customer Support Emails (4 emails)
        support_emails = [
            {
                "from": "support@zendesk.com",
                "subject": "Ticket #ZD-12345 - Account Access Issue Resolved",
                "html_content": """<html><body>
                    <h2>Support Ticket Update</h2>
                    <p>Dear Robert Chen,</p>
                    <p>Good news! Your support ticket has been resolved.</p>
                    <p>Ticket ID: #ZD-12345</p>
                    <p>Issue: Account Access Problem</p>
                    <p>Status: Resolved</p>
                    <p>Your account email: robert.chen@business.com</p>
                    <p>Phone on file: +1-650-555-0199</p>
                    <footer>
                        <p>Zendesk Support Team</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "help@slack.com",
                "subject": "Re: Workspace Setup Assistance",
                "html_content": """<html><body>
                    <h2>Workspace Setup Complete</h2>
                    <p>Hi Maria,</p>
                    <p>Your workspace setup is now complete!</p>
                    <ul>
                        <li>Team workspace: "Marketing Team"</li>
                        <li>Admin email: maria.admin@company.co</li>
                        <li>Phone verification: +1-212-555-0147</li>
                    </ul>
                    <p>Your team can now start collaborating!</p>
                    <footer>
                        <p>Slack Technologies, Inc.</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "support@github.com",
                "subject": "Your GitHub issue has been resolved",
                "html_content": """<html><body>
                    <h2>Issue Resolution</h2>
                    <p>Hello Developer,</p>
                    <p>Your GitHub issue #4567 has been resolved by our team.</p>
                    <p>Issue: Repository access permissions</p>
                    <p>Resolution: Permissions updated successfully</p>
                    <p>Account: developer.coder@tech.com</p>
                    <p>If you need further assistance, please reply to this email.</p>
                    <footer>
                        <p>GitHub Support</p>
                    </footer>
                </body></html>"""
            },
            {
                "from": "customercare@spotify.com",
                "subject": "Your Spotify Premium subscription issue",
                "html_content": """<html><body>
                    <h2>Subscription Update</h2>
                    <p>Hi Music Lover,</p>
                    <p>We've resolved the billing issue with your Spotify Premium subscription.</p>
                    <p>Your account is now active and ready to use.</p>
                    <p>Account email: music.lover@streaming.com</p>
                    <p>Subscription: Spotify Premium Family</p>
                    <p>Next billing date: December 15, 2024</p>
                    <footer>
                        <p>Spotify Customer Care</p>
                    </footer>
                </body></html>"""
            }
        ]
        
        # Combine all emails
        emails.extend(marketing_emails)
        emails.extend(transactional_emails)
        emails.extend(survey_emails)
        emails.extend(personal_emails)
        emails.extend(support_emails)
        
        return emails
    
    def save_emails_to_files(self, emails: List[Dict[str, Any]]) -> List[Path]:
        """Save emails as separate JSON files."""
        file_paths = []
        
        categories = ['marketing'] * 4 + ['transactional'] * 4 + ['survey'] * 4 + ['personal'] * 4 + ['customer_support'] * 4
        
        for i, (email_data, category) in enumerate(zip(emails, categories), 1):
            # Create EmailInput instance for validation
            email_input = EmailInput(**email_data)
            
            # Create filename
            domain = email_input.from_email.split('@')[1].replace('.', '_')
            filename = f"email_{i:02d}_{category}_{domain}.json"
            file_path = self.test_data_dir / filename
            
            # Save as JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(email_input.dict(), f, indent=2, ensure_ascii=False)
            
            file_paths.append(file_path)
            print(f"✅ Saved: {filename}")
        
        return file_paths
    
    def run(self):
        """Generate and save 20 test emails."""
        print("📧 Generating 20 Test Emails")
        print("=" * 40)
        
        # Generate emails
        emails = self.generate_emails()
        print(f"Generated {len(emails)} emails")
        
        # Save to files
        file_paths = self.save_emails_to_files(emails)
        
        print(f"\n✅ Successfully saved {len(file_paths)} email files to {self.test_data_dir}")
        print("\nEmail breakdown:")
        print("  📈 Marketing: 4 emails")
        print("  💳 Transactional: 4 emails")
        print("  📊 Survey: 4 emails")
        print("  👥 Personal: 4 emails")
        print("  🎧 Customer Support: 4 emails")
        
        return file_paths


def main():
    """Main function."""
    generator = EmailGenerator20()
    generator.run()


if __name__ == "__main__":
    main()
