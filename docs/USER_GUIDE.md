# Dora Medical Knowledge Platform - User Guide

**Welcome to Dora** - Your intelligent medical knowledge assistant, designed for Indian physicians.

Version 1.0 | Last Updated: January 2026

---

## 1. Getting Started

### First-Time Login and Setup

**Desktop Application:**
1. Download Dora from the DocAssist portal
2. Install and launch the application
3. Log in with your DocAssist credentials (same as your EMR login)
4. Complete the initial setup wizard

**Mobile Application:**
1. Download from Play Store (Android) or App Store (iOS)
2. Log in with your DocAssist credentials
3. Enable notifications when prompted

### Profile Configuration

**Set Your Specialty:**
- Navigate to **Settings > Profile**
- Select your primary specialty (e.g., Cardiology, Pediatrics, Internal Medicine)
- Add sub-specialties if applicable
- This personalizes your search results and calculator suggestions

**Configure Preferences:**
- **Language:** Choose primary language (English/Hindi)
- **Guideline Preferences:** Select Indian/International guidelines priority
- **Citation Style:** Pick your preferred format (Vancouver, AMA, etc.)
- **Offline Mode:** Enable auto-sync for offline access

### Dashboard Overview

Your dashboard displays:
- **Recent Queries:** Quick access to your search history
- **Saved Answers:** Bookmarked responses
- **Quick Calculators:** Most-used medical calculators
- **Protocol Alerts:** Relevant clinical protocols for your specialty
- **Daily Updates:** New guidelines and research summaries

---

## 2. Querying the Knowledge Base

### How to Ask Medical Questions

**Simple Questions:**
```
"What is the treatment for acute pyelonephritis?"
"Dose of amoxicillin for otitis media in children"
"CHADS-VASc score interpretation"
```

**Complex Clinical Scenarios:**
```
"58-year-old diabetic with eGFR 45, which antibiotics are safe?"
"Management of resistant hypertension in pregnancy"
"Differential diagnosis for fever with thrombocytopenia in monsoon season"
```

**Tips for Better Results:**
- Be specific about patient demographics (age, comorbidities)
- Include relevant lab values or vital signs
- Mention geographic context if relevant ("endemic areas," "Indian guidelines")

### Understanding Citations and Confidence Scores

Each answer includes:
- **Confidence Score:** High (95%+), Medium (80-95%), Low (<80%)
- **Source Citations:** Clickable references to guidelines, textbooks, or journals
- **Last Updated:** When the source was published/reviewed

**Example:**
```
Answer: First-line treatment is oral antibiotics...
Confidence: 96% (High)
Sources:
  [1] Indian Council of Medical Research Guidelines 2025
  [2] UpToDate: Acute Pyelonephritis (Updated Nov 2025)
  [3] NEJM 2024;381:1234-1245
```

**When to Trust the Answer:**
- High confidence + Recent sources = Act with confidence
- Medium confidence = Cross-reference with your clinical judgment
- Low confidence = System flags: "Consider specialist consultation"

### Patient-Contextualized Queries

**Link with DocAssist EMR:**
1. Open patient record in EMR
2. Click **"Ask Dora"** button
3. Your query automatically includes patient's:
   - Age, gender, weight
   - Active medications
   - Allergies
   - Recent lab results
   - Chronic conditions

**Example:**
Instead of typing: "Drug interactions with warfarin in diabetic patient..."
Simply ask: "Can I prescribe ciprofloxacin?" (while patient record is open)
Dora considers: Warfarin interaction, diabetes, renal function, allergies

**Privacy Note:** Patient data stays on your device. Queries use anonymized context.

### Saving Favorite Answers

- Click the **bookmark icon** on any answer
- Access via **Dashboard > Saved Answers**
- Organize with custom tags (e.g., "Pediatric Emergencies," "Antibiotic Protocols")
- Export as PDF for offline reference

---

## 3. Voice Commands

### Activating with "Hey DocAssist"

**Setup (First Time):**
1. Go to **Settings > Voice**
2. Click **"Train Voice Model"**
3. Say "Hey DocAssist" three times
4. Grant microphone permissions

**Using Voice Commands:**
1. Say **"Hey DocAssist"** (works even when app is minimized)
2. Wait for the beep
3. Speak your query naturally
4. Results appear on screen with audio summary

### Supported Voice Commands

**Medical Queries:**
- "Hey DocAssist, what is the dose of metformin for newly diagnosed diabetes?"
- "Hey DocAssist, show me the APGAR score calculator"
- "Hey DocAssist, what are the contraindications for beta blockers?"

**Navigation:**
- "Hey DocAssist, show my recent searches"
- "Hey DocAssist, open cardiovascular calculators"
- "Hey DocAssist, go to clinical protocols"

**Quick Actions:**
- "Hey DocAssist, calculate BMI for 70 kilograms, 165 centimeters"
- "Hey DocAssist, convert 50 milligrams per kilogram for a 12-kilogram child"
- "Hey DocAssist, bookmark this answer"

### Tips for Better Recognition

**Do:**
- Speak clearly at normal pace
- Use medical terms in English (even if speaking Hindi)
- Spell drug names if not recognized: "M-E-T-O-P-R-O-L-O-L"

**Avoid:**
- Speaking too fast
- Mixing languages mid-sentence
- Background noise (use push-to-talk in noisy clinics)

### Troubleshooting Voice Issues

**Voice not activating:**
- Check microphone permissions in system settings
- Ensure app is running in background (mobile)
- Re-train voice model if recognition fails

**Incorrect transcription:**
- Use text mode for rare drug names
- Add custom pronunciations in **Settings > Voice > Medical Dictionary**

**Works offline:** Voice recognition runs locally on your device.

---

## 4. Medical Calculators

### Available Calculators by Category

**Cardiovascular:**
- CHADS-VASc Score (stroke risk in AF)
- HAS-BLED Score (bleeding risk)
- TIMI Risk Score (ACS)
- Framingham Risk Score
- QTc Interval Calculator

**Renal:**
- eGFR (CKD-EPI, MDRD)
- Creatinine Clearance (Cockcroft-Gault)
- FENa (Fractional Excretion of Sodium)
- Kidney Failure Risk Equation

**Endocrine:**
- HbA1c to Average Glucose
- Diabetic Ketoacidosis Severity
- Thyroid Dosing Calculator
- Steroid Conversion

**Pediatric:**
- Pediatric Dosing (by weight)
- Growth Percentiles (WHO/IAP charts)
- Apgar Score
- Bishop Score

**Emergency Medicine:**
- Glasgow Coma Scale
- CURB-65 (pneumonia severity)
- Wells Score (DVT/PE)
- SIRS Criteria

**And 50+ more...** Browse by specialty in the Calculators tab.

### How to Use Calculators

**Method 1: Search**
- Type calculator name in search bar
- Or describe what you need: "GFR calculator"

**Method 2: Voice**
- "Hey DocAssist, calculate CHADS-VASc score"
- Then provide values when prompted

**Method 3: EMR Integration**
- Open patient record
- Click **"Quick Calculator"**
- Relevant data auto-fills from patient chart

**Example: eGFR Calculator**
1. Open **Calculators > Renal > eGFR**
2. Enter: Creatinine (mg/dL), Age, Gender
3. Results show:
   - eGFR value with CKD stage
   - Drug dosing adjustments needed
   - Referral recommendations

### Saving Calculation History

- All calculations auto-save to **History** tab
- Link calculations to patient records (optional)
- Export results to patient notes with one click
- Set reminders for recalculation (e.g., "Repeat HbA1c in 3 months")

---

## 5. Clinical Protocols

### Finding Protocols by Specialty

**Browse by Specialty:**
- Navigate to **Protocols** tab
- Filter by your specialty or view all
- Search by condition (e.g., "sepsis protocol")

**Available Protocol Libraries:**
- Indian Council of Medical Research (ICMR)
- WHO Essential Care Guidelines
- Surviving Sepsis Campaign
- AHA/ESC Cardiology Guidelines
- Your hospital's custom protocols (if configured)

### Using Checklists

**Interactive Protocols:**
1. Open protocol (e.g., "Sepsis Resuscitation Bundle")
2. Each step has a checkbox
3. Tap to mark complete
4. Timestamps auto-record
5. Export summary to patient chart

**Example: Stroke Thrombolysis Checklist**
```
☐ Symptom onset <4.5 hours?
☐ CT brain shows no hemorrhage?
☐ Blood pressure <185/110?
☐ No recent surgery/trauma?
☐ Platelet count >100,000?
...
☑ All criteria met → Proceed with thrombolysis
```

### Tracking Protocol Completion

- **Real-time tracking:** See time elapsed for each step
- **Alerts:** System notifies if critical time windows are passing
- **Compliance reports:** Review your protocol adherence (for audit/CME)
- **Team collaboration:** Share checklist status with nursing staff

---

## 6. Document Management

### Uploading Your Own Documents

**Supported Formats:**
- PDF (textbooks, guidelines, research papers)
- DOCX (case reports, notes)
- Images (flowcharts, diagrams)

**How to Upload:**
1. Click **Library > Upload Document**
2. Select file or drag-and-drop
3. Add tags (e.g., "Cardiology," "Guidelines 2025")
4. Choose privacy: Personal library or share with team
5. System processes and indexes (2-5 minutes for large PDFs)

**What Happens:**
- Text is extracted and made searchable
- Figures and tables are preserved
- Document becomes part of your queryable knowledge base

**Example Use Case:**
Upload your medical college notes → Now you can ask: "What did I learn about diabetic nephropathy in my nephrology rotation?"

### Annotations and Highlighting

**While Reading:**
- Highlight text with cursor (desktop) or long-press (mobile)
- Choose color: Yellow (important), Red (critical), Green (to review)
- Add personal notes to any section
- Annotations sync across devices

**Smart Features:**
- Ask questions about highlighted sections: "Explain this mechanism"
- Link highlights to patient cases
- Export all highlights as summary PDF

### Audio Overview (Podcast) Generation

**Turn Documents into Audio:**
1. Open any document
2. Click **"Generate Audio Overview"**
3. Choose:
   - Full document or selected pages
   - Summary depth (5 min / 15 min / 30 min)
   - Voice speed (0.8x to 1.5x)
4. System creates podcast-style overview

**Perfect For:**
- Commute learning
- Pre-reading for conferences
- Quick guideline reviews

**Languages:** English and Hindi audio available

### Document Comparison

**Compare Guidelines:**
1. Select 2-3 documents
2. Click **"Compare"**
3. System highlights:
   - Key differences in recommendations
   - Conflicting evidence
   - Common ground

**Example:**
Compare Indian vs. International hypertension guidelines:
- Threshold differences
- First-line drug preferences
- Monitoring recommendations

---

## 7. Offline Mode

### What Works Offline

**Full Functionality:**
- Medical calculators (all)
- Clinical protocols and checklists
- Previously viewed documents
- Voice commands and queries

**Limited Functionality:**
- New queries use local AI (Qwen 2.5 model)
  - Still accurate but may have less recent data
  - No internet-based sources cited
- Cannot upload new documents
- No real-time guideline updates

### Syncing When Back Online

**Automatic Sync:**
- App detects internet connection
- Uploads any offline queries/calculations
- Downloads latest guideline updates
- Syncs bookmarks and annotations

**Manual Sync:**
- Pull down on dashboard to force refresh
- Check sync status in **Settings > Offline Mode**

### Managing Offline Storage

**Pre-download for Offline:**
1. Go to **Settings > Offline Mode**
2. Select content to cache:
   - Essential calculators (50 MB)
   - Clinical protocols (200 MB)
   - My uploaded documents (varies)
   - Specialty-specific guidelines (500 MB)
3. Click **"Download for Offline Use"**

**Storage Tips:**
- Mobile: Download essentials only (limited storage)
- Desktop: Can cache entire knowledge base (5-10 GB)
- Clear cache periodically to free space

**Offline works anywhere:** Rural areas, flights, no-network zones.

---

## 8. Mobile App

### Key Differences from Desktop

**Mobile-Optimized Features:**
- **Quick Actions Widget:** Add to home screen for instant calculator access
- **Camera Integration:** Snap photos of lab reports → Auto-extract values
- **Offline-first design:** Works seamlessly without connectivity
- **One-handed mode:** Swipe gestures for fast navigation

**Desktop-Exclusive Features:**
- Multi-window view (compare documents side-by-side)
- Batch document uploads
- Advanced analytics and reports

### Push Notifications

**What You'll Receive:**
- **Critical Alerts:** Drug recalls, safety alerts (CDSCO)
- **Guideline Updates:** When protocols change
- **Reminders:** Follow-up calculations, protocol reviews
- **Research Updates:** New studies in your specialty (weekly digest)

**Customize Notifications:**
- Go to **Settings > Notifications**
- Choose categories and frequency
- Set "Do Not Disturb" hours

### Quick Actions

**Shortcuts for Common Tasks:**
- Shake phone → Activate voice
- Long-press app icon → Quick calculators menu
- Screenshot → "Extract data from image"
- Share from EMR → Opens in Dora for analysis

**Mobile Widgets:**
- Today's medical fact
- Quick calculator (set your favorite)
- Recent searches
- Protocol reminders

---

## 9. Subscription & Billing

### Plans Overview

**Individual Plan:**
- **Price:** ₹999/month or ₹9,999/year (save 17%)
- **Includes:**
  - Unlimited queries
  - All calculators and protocols
  - 10 GB document storage
  - Voice commands
  - EMR integration
  - Mobile + Desktop apps
  - Email support

**Group Practice Plan:**
- **Price:** ₹7,999/month (up to 10 doctors)
- **Additional:**
  - Shared protocol library
  - Team collaboration features
  - 100 GB shared storage
  - Priority support
  - Custom protocol uploads
  - Admin dashboard

**Hospital/Institution:**
- Custom pricing based on number of users
- Contact: sales@docassist.in
- Includes training and onboarding

**Free Trial:** 30 days, no credit card required

### Managing Your Subscription

**Upgrade/Downgrade:**
1. Go to **Settings > Subscription**
2. Click **"Change Plan"**
3. Select new plan
4. Changes take effect immediately (pro-rated billing)

**Cancel Subscription:**
- Access until end of billing period
- Export all your data before cancellation
- No cancellation fees

**Billing Cycle:**
- Monthly: Charged on same date each month
- Annual: One-time charge, auto-renews yearly
- Receive invoice via email

### Payment Methods

**Accepted:**
- Credit/Debit Cards (Visa, Mastercard, RuPay)
- UPI (Google Pay, PhonePe, Paytm)
- Net Banking
- International cards accepted

**Auto-renewal:**
- Enabled by default
- Disable in **Settings > Billing**
- Reminder email sent 7 days before renewal

### Invoices and Receipts

**Download Invoices:**
- **Settings > Billing > Invoice History**
- PDF format with GST details
- Use for tax deductions (professional expense)

**GST Information:**
- Add your GSTIN in **Settings > Billing > Tax Details**
- GST invoices generated automatically
- Monthly consolidated invoice available

---

## 10. Privacy & Security

### HIPAA Compliance

**Data Protection:**
- All patient data encrypted (AES-256)
- Transmission via TLS 1.3
- No patient identifiers leave your device without consent
- Compliant with DISHA (Digital Information Security in Healthcare Act)

**Audit Logs:**
- Every access tracked with timestamp
- Review your activity in **Settings > Security > Activity Log**
- Required for regulatory compliance

### Data Ownership

**You Own Your Data:**
- All queries, documents, annotations belong to you
- DocAssist does NOT train AI models on your data
- No third-party sharing without explicit consent

**How We Use Data:**
- Anonymous usage statistics to improve app (opt-out available)
- Aggregate data for feature prioritization
- No individual-level data analysis

### Export Your Data

**Anytime Export:**
1. Go to **Settings > Data & Privacy > Export Data**
2. Choose what to export:
   - Query history
   - Saved answers and bookmarks
   - Uploaded documents
   - Calculation history
   - Annotations
3. Click **"Request Export"**
4. Receive download link via email (within 24 hours)
5. Data provided in standard formats (JSON, PDF, CSV)

**Transfer to Another Provider:**
- Fully portable data format
- No lock-in period
- Export available even after subscription ends (90-day grace period)

**Delete Your Data:**
- **Settings > Data & Privacy > Delete Account**
- Permanent deletion within 30 days
- Cannot be reversed

---

## 11. Getting Help

### In-App Support

**Help Center:**
- Click **"?"** icon in top-right corner
- Searchable knowledge base
- Video tutorials
- FAQs by category

**Live Chat:**
- Available 9 AM - 9 PM IST (Mon-Sat)
- Click **"Chat with Support"**
- Average response time: <5 minutes

**Screen Sharing:**
- For complex issues, support can request screen-share
- You control when to start/stop
- Available during business hours

### Contact Information

**Email Support:**
- support@docassist.in
- Response time: <24 hours (weekdays)
- Attach screenshots for faster resolution

**Phone Support:**
- Premium/Group plans only
- +91-XXXX-XXXXXX (toll-free)
- Mon-Fri, 10 AM - 6 PM IST

**WhatsApp:**
- Quick questions: +91-XXXXX-XXXXX
- Business hours support
- No patient data via WhatsApp (privacy policy)

### Reporting Issues

**Bug Reports:**
1. Click **Settings > Help > Report a Problem**
2. Describe the issue
3. System auto-attaches:
   - Error logs
   - Device information
   - Recent activity (anonymized)
4. Track status via email updates

**Feature Requests:**
- Submit via **Settings > Help > Suggest a Feature**
- Vote on community feature board
- Top requests prioritized for development

**Medical Content Errors:**
- If you find incorrect/outdated medical information:
- Click **"Report Error"** on the answer
- Our clinical team reviews within 48 hours
- You receive update when corrected

### Community Resources

**Dora User Forum:**
- community.docassist.in
- Share tips and workflows
- Monthly "Tip of the Month" contest
- Moderated by physicians

**Training Webinars:**
- Monthly live sessions
- "Mastering Dora" series
- CME credits available (IMA recognized)
- Register: training.docassist.in

**Social Media:**
- Twitter: @DocAssistIndia
- YouTube: Product updates and tutorials
- LinkedIn: Professional discussions

---

## Appendix: Quick Reference

### Keyboard Shortcuts (Desktop)

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | New query |
| `Ctrl/Cmd + S` | Bookmark current answer |
| `Ctrl/Cmd + F` | Search within document |
| `Ctrl/Cmd + H` | View history |
| `Ctrl/Cmd + ,` | Settings |
| `Ctrl/Cmd + /` | Show all shortcuts |

### Voice Command Cheat Sheet

- "Hey DocAssist, **calculate** [calculator name]"
- "Hey DocAssist, **show me** [protocol/guideline]"
- "Hey DocAssist, **what is** [medical question]"
- "Hey DocAssist, **open** [feature name]"
- "Hey DocAssist, **bookmark this**"

### Emergency Quick Access

**Time-Critical Situations:**
- Type **"emergency"** in search → Instant access to ACLS, stroke, sepsis protocols
- Voice: "Hey DocAssist, emergency protocols"
- Mobile widget: Long-press → Emergency Calculators

---

## Welcome to Smarter Medicine

Dora is designed to make you a more informed, efficient, and confident physician. We're continuously improving based on your feedback.

**Need help getting started?**
Book a free 15-minute onboarding call: onboarding@docassist.in

**Have feedback?**
We'd love to hear from you: feedback@docassist.in

---

*DocAssist Dora v1.0 | Built for Indian Physicians | © 2026 DocAssist Health Technologies Pvt. Ltd.*
*HIPAA Compliant | DISHA Compliant | ISO 27001 Certified*
