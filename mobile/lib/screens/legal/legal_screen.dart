/// Legal Documents Screen
///
/// Privacy Policy, Terms of Service, Refund Policy, and other legal pages.

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../theme.dart';

class LegalScreen extends StatelessWidget {
  final String title;
  final String documentType;

  const LegalScreen({
    super.key,
    required this.title,
    required this.documentType,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: MarkdownBody(
          data: _getDocument(documentType),
          styleSheet: MarkdownStyleSheet(
            h1: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            h2: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            h3: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            p: const TextStyle(fontSize: 14, height: 1.6),
          ),
        ),
      ),
    );
  }

  String _getDocument(String type) {
    switch (type) {
      case 'privacy':
        return _privacyPolicy;
      case 'terms':
        return _termsOfService;
      case 'refund':
        return _refundPolicy;
      case 'data':
        return _dataProcessing;
      case 'hipaa':
        return _hipaaNotice;
      default:
        return 'Document not found.';
    }
  }
}

const String _privacyPolicy = '''
# Privacy Policy

**Last Updated: January 2026**

DocAssist Healthcare Technologies Private Limited ("we", "us", or "DocAssist") is committed to protecting the privacy of healthcare professionals and their patients. This Privacy Policy explains how we collect, use, and protect your information when you use DocAssist Dora ("the Service").

## 1. Information We Collect

### 1.1 Account Information
- Name and professional credentials
- Email address and phone number
- Medical license number and specialty
- Hospital/clinic affiliation

### 1.2 Usage Data
- Queries submitted to the knowledge base
- Documents uploaded for analysis
- Feature usage and interaction patterns
- Device and browser information

### 1.3 Payment Information
- Billing address and GSTIN
- Payment method details (processed by Razorpay)
- Transaction history

## 2. How We Use Your Information

We use your information to:
- Provide and improve the medical knowledge service
- Personalize content based on your specialty
- Process payments and manage subscriptions
- Send important service updates
- Comply with legal and regulatory requirements
- Conduct anonymized research to improve medical AI

## 3. Data Security

### 3.1 Technical Safeguards
- End-to-end encryption for all data transmission
- AES-256 encryption for data at rest
- Regular security audits and penetration testing
- SOC 2 Type II certified infrastructure

### 3.2 Access Controls
- Role-based access control (RBAC)
- Multi-factor authentication available
- Audit logs for all data access
- Automatic session timeout

## 4. Patient Data Protection

### 4.1 No Patient Data Storage
We do NOT store identifiable patient information. All patient data processing happens locally on your device or is immediately anonymized.

### 4.2 HIPAA Compliance
For users in the United States, we comply with HIPAA regulations. We offer Business Associate Agreements (BAA) for enterprise customers.

### 4.3 DISHA Compliance
For users in India, we comply with the Digital Information Security in Healthcare Act (DISHA) requirements.

## 5. Data Retention

- Account data: Retained while account is active + 3 years
- Query history: 2 years (can be deleted on request)
- Payment records: 7 years (as per tax regulations)
- Usage analytics: 1 year (anonymized)

## 6. Your Rights

You have the right to:
- Access your personal data
- Correct inaccurate data
- Delete your account and data
- Export your data in machine-readable format
- Opt out of marketing communications
- Withdraw consent at any time

## 7. Data Sharing

We DO NOT sell your data. We may share data with:
- Payment processors (Razorpay) for transactions
- Cloud providers (AWS) for infrastructure
- Analytics services (in anonymized form)
- Law enforcement when legally required

## 8. Cookies and Tracking

We use essential cookies for authentication and session management. We use analytics cookies to improve the service (can be disabled in settings).

## 9. International Data Transfers

Data may be processed in India, USA, and Singapore. We use standard contractual clauses for international transfers.

## 10. Children's Privacy

The Service is intended for licensed healthcare professionals. We do not knowingly collect data from persons under 18 years of age.

## 11. Changes to This Policy

We will notify you of significant changes via email at least 30 days before they take effect.

## 12. Contact Us

**Data Protection Officer:**
Email: dpo@docassist.in
Address: DocAssist Healthcare Technologies Pvt Ltd
123 Tech Park, Bangalore 560001, India

**For EU Users:**
EU Representative: [Contact details]

---

*This policy is available in Hindi, Tamil, Telugu, Bengali, and Marathi.*
''';

const String _termsOfService = '''
# Terms of Service

**Last Updated: January 2026**

Welcome to DocAssist Dora. These Terms of Service ("Terms") govern your use of the DocAssist Dora medical knowledge platform ("Service") provided by DocAssist Healthcare Technologies Private Limited ("Company", "we", "us").

## 1. Acceptance of Terms

By accessing or using the Service, you agree to be bound by these Terms. If you disagree with any part, you may not access the Service.

## 2. Eligibility

The Service is available only to:
- Licensed healthcare professionals
- Medical students (with institutional access)
- Healthcare organizations

You must provide valid professional credentials during registration.

## 3. Account Registration

### 3.1 Account Creation
- You must provide accurate and complete information
- You are responsible for maintaining account security
- You must not share your account credentials
- You must notify us immediately of any unauthorized access

### 3.2 Verification
We may verify your medical license and credentials. False information will result in account termination.

## 4. Subscription and Payments

### 4.1 Subscription Plans
- Subscriptions are billed monthly, quarterly, or annually
- Prices are in Indian Rupees and include GST
- We reserve the right to change prices with 30 days notice

### 4.2 Payment
- Payments are processed by Razorpay
- Failed payments may result in service suspension
- You are responsible for all applicable taxes

### 4.3 Cancellation
- Cancel anytime from your account settings
- Access continues until the end of the billing period
- No partial refunds for early cancellation

## 5. Acceptable Use

You agree NOT to:
- Use the Service for illegal purposes
- Share account access with unauthorized users
- Attempt to reverse engineer the Service
- Use the Service to diagnose or treat patients without professional judgment
- Upload malicious content or viruses
- Scrape or mass download content
- Resell or redistribute the Service

## 6. Medical Disclaimer

### 6.1 Not Medical Advice
The Service provides medical information for educational purposes only. It is NOT a substitute for professional medical judgment, diagnosis, or treatment.

### 6.2 Clinical Responsibility
YOU are responsible for all clinical decisions. The Service is a reference tool to support, not replace, your professional judgment.

### 6.3 No Warranties
We do not warrant that the information is complete, accurate, or current. Medical knowledge evolves, and you should verify critical information from multiple sources.

## 7. Intellectual Property

### 7.1 Our Content
All content in the Service (except user-uploaded content) is owned by DocAssist or licensed to us. You may not copy, modify, or distribute our content without permission.

### 7.2 Your Content
You retain ownership of content you upload. You grant us a license to process and display your content for providing the Service.

### 7.3 Feedback
Any feedback or suggestions you provide may be used by us without obligation to you.

## 8. Privacy

Your use of the Service is subject to our Privacy Policy. By using the Service, you consent to our data practices.

## 9. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW:
- The Service is provided "AS IS" without warranties
- We are not liable for indirect, incidental, or consequential damages
- Our total liability shall not exceed the fees paid by you in the past 12 months

## 10. Indemnification

You agree to indemnify and hold harmless DocAssist from any claims arising from:
- Your use of the Service
- Your violation of these Terms
- Your violation of any third-party rights

## 11. Termination

### 11.1 By You
You may close your account at any time.

### 11.2 By Us
We may suspend or terminate your account for:
- Violation of these Terms
- Non-payment
- Fraudulent activity
- At our discretion with 30 days notice

### 11.3 Effect of Termination
Upon termination, your right to use the Service ceases immediately. We may retain certain data as required by law.

## 12. Dispute Resolution

### 12.1 Governing Law
These Terms are governed by the laws of India.

### 12.2 Arbitration
Disputes shall be resolved by binding arbitration in Bangalore, India, under the Arbitration and Conciliation Act, 1996.

## 13. Changes to Terms

We may modify these Terms at any time. Material changes will be notified via email 30 days in advance. Continued use constitutes acceptance.

## 14. General Provisions

- These Terms constitute the entire agreement
- Our failure to enforce any right is not a waiver
- If any provision is invalid, the rest remains in effect
- You may not assign these Terms without our consent

## 15. Contact

For questions about these Terms:
Email: legal@docassist.in
Address: DocAssist Healthcare Technologies Pvt Ltd
123 Tech Park, Bangalore 560001, India

---

*Effective Date: January 1, 2026*
''';

const String _refundPolicy = '''
# Refund Policy

**Last Updated: January 2026**

This Refund Policy explains how refunds are handled for DocAssist Dora subscriptions.

## 1. Free Trial

### 1.1 Trial Period
New users receive a 7-day free trial of the Professional plan. No credit card is required for the trial.

### 1.2 No Charge
You will not be charged during the trial period. You may cancel at any time without any obligation.

## 2. Subscription Refunds

### 2.1 Monthly Subscriptions
- **First 7 days:** Full refund if not satisfied
- **After 7 days:** No refunds, but you retain access until the end of the billing period

### 2.2 Quarterly Subscriptions
- **First 14 days:** Full refund if not satisfied
- **After 14 days:** Pro-rata refund may be considered on a case-by-case basis

### 2.3 Annual Subscriptions
- **First 30 days:** Full refund if not satisfied
- **After 30 days:** Pro-rata refund for remaining months, less a 10% processing fee

## 3. How to Request a Refund

To request a refund:
1. Email billing@docassist.in with your account email
2. Include your reason for the refund request
3. We will process your request within 5-7 business days

## 4. Refund Processing

### 4.1 Processing Time
- Approved refunds are processed within 7 business days
- Bank credits may take an additional 5-10 business days

### 4.2 Refund Method
Refunds are credited to the original payment method (card, UPI, net banking).

## 5. Non-Refundable Cases

Refunds are NOT provided for:
- Account termination due to Terms of Service violation
- Partial months after the refund window
- Add-on purchases (storage, API credits)
- Enterprise custom contracts (see individual agreement)

## 6. Subscription Cancellation

### 6.1 How to Cancel
Cancel anytime from Settings > Subscription > Cancel Subscription

### 6.2 Access After Cancellation
Your access continues until the end of your current billing period. Data can be exported for 30 days after cancellation.

## 7. Chargebacks

If you dispute a charge with your bank:
- Your account will be suspended pending investigation
- Valid chargebacks will be honored
- Fraudulent chargebacks may result in permanent account termination

## 8. Price Guarantee

If we reduce prices within 30 days of your purchase, contact us for a price adjustment or credit.

## 9. Special Circumstances

We may provide refunds or credits in exceptional circumstances:
- Extended service outages (>24 hours)
- Critical bugs affecting your workflow
- Other situations at our discretion

## 10. Contact

For billing questions or refund requests:
- Email: billing@docassist.in
- Phone: +91-80-XXXX-XXXX
- Support hours: Mon-Fri, 9 AM - 6 PM IST

---

*This policy is subject to change. Material changes will be communicated via email.*
''';

const String _dataProcessing = '''
# Data Processing Agreement

**Last Updated: January 2026**

This Data Processing Agreement ("DPA") is part of the Terms of Service between you and DocAssist Healthcare Technologies Private Limited.

## 1. Definitions

- **Controller:** You, the healthcare professional using the Service
- **Processor:** DocAssist, processing data on your behalf
- **Personal Data:** Any information relating to an identified or identifiable natural person
- **Processing:** Any operation performed on personal data

## 2. Scope of Processing

### 2.1 Types of Data Processed
- Healthcare professional profile data
- Medical queries and search history
- Uploaded documents (anonymized)
- Usage and analytics data

### 2.2 Patient Data
We do NOT process identifiable patient data. Any patient information must be de-identified before upload.

## 3. Processing Purposes

We process data only for:
- Providing the medical knowledge service
- Improving and personalizing the service
- Analytics and performance optimization
- Billing and account management
- Legal compliance

## 4. Security Measures

We implement appropriate technical and organizational measures:
- Encryption in transit (TLS 1.3) and at rest (AES-256)
- Access controls and authentication
- Regular security assessments
- Employee training
- Incident response procedures

## 5. Sub-processors

We use the following sub-processors:
- **AWS (India):** Cloud infrastructure
- **Razorpay (India):** Payment processing
- **Anthropic (USA):** AI processing (no data retained)

## 6. Data Subject Rights

We assist you in responding to data subject requests for:
- Access to personal data
- Rectification of inaccurate data
- Erasure ("right to be forgotten")
- Data portability
- Restriction of processing

## 7. Data Breach Notification

In case of a personal data breach:
- We will notify you within 72 hours
- We will provide details of the breach
- We will assist with regulatory notifications

## 8. Data Transfers

For international data transfers, we use:
- Standard Contractual Clauses (SCCs)
- Appropriate safeguards as required by law

## 9. Audit Rights

Enterprise customers may conduct audits with reasonable notice. We provide SOC 2 Type II reports upon request.

## 10. Term and Termination

This DPA terminates when the main agreement terminates. Upon termination, we will delete or return your data as requested.

---

*For a signed copy of this DPA, contact legal@docassist.in*
''';

const String _hipaaNotice = '''
# HIPAA Notice

**Last Updated: January 2026**

This notice applies to users in the United States who are covered entities or business associates under the Health Insurance Portability and Accountability Act (HIPAA).

## 1. Our Commitment to HIPAA

DocAssist is committed to helping healthcare providers maintain HIPAA compliance when using our Service.

## 2. Business Associate Agreement

### 2.1 Availability
We offer Business Associate Agreements (BAA) to:
- Enterprise plan subscribers
- Healthcare organizations
- Covered entities as defined by HIPAA

### 2.2 How to Request
Contact sales@docassist.in to request a BAA.

## 3. Protected Health Information (PHI)

### 3.1 Important Note
DocAssist Dora is designed as a **reference tool** and does NOT require PHI to function.

### 3.2 Recommendation
We strongly recommend:
- Do NOT enter identifiable PHI in queries
- De-identify all patient information before upload
- Use our HIPAA-compliant workspace features

## 4. Technical Safeguards

For HIPAA compliance, we provide:
- End-to-end encryption
- Audit logging
- Access controls
- Automatic session timeout
- Secure data centers

## 5. Administrative Safeguards

We maintain:
- Security policies and procedures
- Employee training programs
- Incident response plans
- Regular risk assessments

## 6. Your Responsibilities

As a covered entity, you are responsible for:
- Maintaining your own HIPAA compliance program
- Training your staff on PHI handling
- Not entering identifiable PHI unnecessarily
- Reporting any suspected breaches

## 7. Breach Notification

In the event of a breach involving PHI:
- We will notify you within 60 days
- We will provide required breach details
- We will cooperate with your notification efforts

## 8. Contact

For HIPAA-related questions:
- Email: hipaa@docassist.in
- Security: security@docassist.in

---

*This notice is for informational purposes. Consult your legal counsel for specific compliance requirements.*
''';

/// Legal documents hub screen
class LegalHubScreen extends StatelessWidget {
  const LegalHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Legal & Privacy'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildLegalItem(
            context,
            icon: Icons.privacy_tip,
            title: 'Privacy Policy',
            subtitle: 'How we collect, use, and protect your data',
            documentType: 'privacy',
          ),
          _buildLegalItem(
            context,
            icon: Icons.description,
            title: 'Terms of Service',
            subtitle: 'Rules and conditions for using Dora',
            documentType: 'terms',
          ),
          _buildLegalItem(
            context,
            icon: Icons.money_off,
            title: 'Refund Policy',
            subtitle: 'Cancellation and refund procedures',
            documentType: 'refund',
          ),
          _buildLegalItem(
            context,
            icon: Icons.storage,
            title: 'Data Processing Agreement',
            subtitle: 'How we handle data processing',
            documentType: 'data',
          ),
          _buildLegalItem(
            context,
            icon: Icons.security,
            title: 'HIPAA Notice',
            subtitle: 'For US healthcare providers',
            documentType: 'hipaa',
          ),
        ],
      ),
    );
  }

  Widget _buildLegalItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required String documentType,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: DoraColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: DoraColors.primary),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(
          subtitle,
          style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => LegalScreen(title: title, documentType: documentType),
          ),
        ),
      ),
    );
  }
}
