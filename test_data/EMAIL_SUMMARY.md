# Test Email Dataset Summary

## 📧 **20 Generated Emails**

Successfully generated 20 diverse test emails across all categories, saved as separate JSON files in the `test_data/` directory.

### 📊 **Email Distribution**

#### **Marketing Emails (4 emails)**
1. `email_01_marketing_shopify_com.json` - Black Friday Sale
2. `email_02_marketing_techcrunch_com.json` - Tech Newsletter
3. `email_03_marketing_amazon_com.json` - Prime Day Deals
4. `email_04_marketing_netflix_com.json` - New Content Promotion

#### **Transactional Emails (4 emails)**
5. `email_05_transactional_amazon_com.json` - Order Confirmation
6. `email_06_transactional_stripe_com.json` - Payment Receipt
7. `email_07_transactional_paypal_com.json` - Payment Received
8. `email_08_transactional_uber_com.json` - Trip Receipt

#### **Survey Emails (4 emails)**
9. `email_09_survey_surveymonkey_com.json` - Feedback Survey
10. `email_10_survey_typeform_com.json` - Product Research
11. `email_11_survey_google_com.json` - Opinion Rewards
12. `email_12_survey_airbnb_com.json` - Stay Review

#### **Personal Emails (4 emails)**
13. `email_13_personal_family_com.json` - Family Reunion
14. `email_14_personal_personal_net.json` - Coffee Meetup
15. `email_15_personal_alumni_edu.json` - Class Reunion
16. `email_16_personal_community_org.json` - Neighborhood BBQ

#### **Customer Support Emails (4 emails)**
17. `email_17_customer_support_zendesk_com.json` - Ticket Resolution
18. `email_18_customer_support_slack_com.json` - Workspace Setup
19. `email_19_customer_support_github_com.json` - Issue Resolution
20. `email_20_customer_support_spotify_com.json` - Subscription Update

## 🏗️ **JSON Structure**

Each email file contains exactly three fields as requested:

```json
{
  "from": "sender@domain.com",
  "subject": "Email Subject Line",
  "html_content": "<html><body>Email content with HTML formatting</body></html>"
}
```

## 📋 **Content Features**

### **Realistic Data**
- **Email Addresses**: Realistic sender addresses from known companies
- **Subject Lines**: Authentic subject lines with emojis and formatting
- **HTML Content**: Proper HTML structure with headers, paragraphs, links, and footers

### **PII Data Included**
Each email contains various types of PII data for testing:
- **Email addresses**: Customer emails, contact emails
- **Phone numbers**: Various formats (US, international)
- **Names**: Customer names, contact persons
- **Addresses**: Business addresses, delivery addresses
- **Transaction IDs**: Order numbers, payment references

### **Business Information**
- **Company names**: Real company names (Shopify, Amazon, Netflix, etc.)
- **Websites**: Company websites and unsubscribe links
- **Industries**: Technology, e-commerce, entertainment, etc.
- **Locations**: Various geographic locations

## 🎯 **Testing Scenarios**

These emails are designed to test:

1. **Email Classification**: Accurate categorization across all 5 categories
2. **PII Detection**: Various PII types in different formats
3. **Business Entity Extraction**: Company information extraction
4. **HTML Processing**: HTML stripping and content extraction
5. **Metadata Extraction**: Domain, URL, and footer extraction
6. **Vector Similarity**: Similar content matching
7. **Confidence Scoring**: Classification confidence assessment

## 🚀 **Usage**

These emails can be used with the email processing pipeline:

```bash
# Process all emails
python scripts/run_email_processing.py

# Test specific functionality
python scripts/test_llm_providers.py

# Run health checks
python scripts/health_check.py
```

## ✅ **Quality Assurance**

- **Valid JSON**: All files contain valid JSON structure
- **Required Fields**: All files have `from`, `subject`, and `html_content` fields
- **Diverse Content**: Wide variety of content types and styles
- **Realistic Data**: Based on real-world email patterns
- **Balanced Distribution**: Equal representation across all categories

The dataset is ready for comprehensive testing of the email processing pipeline!
