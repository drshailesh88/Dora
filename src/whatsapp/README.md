# WhatsApp Integration for Dora

Complete WhatsApp Business Cloud API integration for the Dora medical knowledge platform.

## Overview

This module enables doctors to interact with Dora through WhatsApp, providing:

- **Text & Voice Queries**: Ask medical questions via text or voice notes
- **Drug Interaction Checks**: Quick medication interaction screening
- **Medical Calculators**: Access common clinical calculators
- **Answer Sharing**: Share information with patients
- **Account Linking**: Connect WhatsApp to Dora account for premium features
- **Notifications**: Receive important updates
- **Group Features**: Team collaboration and broadcasts

## Architecture

```
whatsapp/
├── models.py          # Data models (User, Message, Conversation, etc.)
├── client.py          # WhatsApp Cloud API client
├── webhook.py         # Webhook handler and parser
├── conversation.py    # Conversation state management
├── handlers.py        # Message type handlers
├── templates.py       # Message formatting templates
├── media.py           # Media handling (voice, images, PDFs)
├── sharing.py         # Answer sharing with patients
├── groups.py          # Group/team features
├── service.py         # Main service coordinator
└── __init__.py        # Clean exports
```

## Setup

### 1. Meta WhatsApp Business Account

1. Create a Meta Business account at https://business.facebook.com
2. Set up WhatsApp Business API
3. Get your credentials:
   - Access Token
   - Phone Number ID
   - Business Account ID
   - App Secret
   - Webhook Verify Token

### 2. Environment Variables

Add to your `.env` file:

```bash
# WhatsApp Cloud API Credentials
WHATSAPP_ACCESS_TOKEN=your_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_VERIFY_TOKEN=your_verify_token
```

### 3. Webhook Configuration

1. In Meta Developer Console, configure webhook URL:
   ```
   https://your-domain.com/api/whatsapp/webhook
   ```

2. Subscribe to webhook fields:
   - `messages`
   - `message_status`

3. Verify webhook using the verify token

### 4. API Integration

The WhatsApp router is automatically included in the FastAPI app.

```python
from src.whatsapp import WhatsAppService

# Initialize service
service = WhatsAppService()

# Process incoming message
await service.process_message(message)
```

## Usage

### Basic Setup

```python
from src.whatsapp import WhatsAppService, WhatsAppClient
from src.core.pipeline import MedicalQueryPipeline
from src.drugs import DrugInteractionChecker

# Initialize with dependencies
query_pipeline = MedicalQueryPipeline()
drug_checker = DrugInteractionChecker()

service = WhatsAppService(
    query_pipeline=query_pipeline,
    drug_checker=drug_checker,
)
```

### Sending Messages

```python
from src.whatsapp import WhatsAppClient, QuickReply

client = WhatsAppClient()

# Send text message
await client.send_text(
    to="919876543210",
    text="Hello from Dora!",
)

# Send with buttons
buttons = [
    QuickReply(id="query", title="Ask Question"),
    QuickReply(id="drugs", title="Check Drugs"),
]

await client.send_interactive_buttons(
    to="919876543210",
    body="How can I help you?",
    buttons=buttons,
)

# Send image
await client.send_image(
    to="919876543210",
    image_url="https://example.com/image.jpg",
    caption="Medical diagram",
)

# Send document
await client.send_document(
    to="919876543210",
    document_url="https://example.com/report.pdf",
    filename="Lab Report.pdf",
)
```

### Handling Webhooks

```python
from src.whatsapp import WebhookHandler

handler = WebhookHandler(
    app_secret="your_app_secret",
    verify_token="your_verify_token",
)

# Verify webhook (GET request)
challenge = handler.verify_webhook(mode, token, challenge)

# Handle incoming webhook (POST request)
result = handler.handle_webhook(payload, signature)

# Process messages
for message in result['messages']:
    await service.process_message(message)
```

### Conversation Management

```python
from src.whatsapp import ConversationManager

conv_manager = ConversationManager()

# Get or create user
user = conv_manager.get_or_create_user("919876543210")

# Generate link code
code = conv_manager.generate_link_code("919876543210")
# Send code to user via WhatsApp

# Link account
conv_manager.link_user("919876543210", user_id="user_123")

# Manage conversation state
conv = conv_manager.get_or_create_conversation("919876543210")
conv_manager.set_context("919876543210", "last_query", "amoxicillin dose")
```

### Media Handling

```python
from src.whatsapp import MediaHandler

media_handler = MediaHandler(whatsapp_client=client)

# Transcribe voice note
text = await media_handler.transcribe_voice_note(
    media_id="voice_note_id",
    language="en",
)

# Generate audio response
audio_path = await media_handler.generate_audio_response(
    text="This is the answer to your question.",
)

# Upload and send
media_id = await client.upload_media(audio_path, "audio/ogg")
await client.send_audio(to="919876543210", audio_id=media_id)

# Process image
result = await media_handler.process_image(media_id="image_id")

# Generate PDF handout
pdf_path = await media_handler.generate_pdf_handout(
    content="Medical information...",
    title="Patient Handout",
)
```

### Answer Sharing

```python
from src.whatsapp import AnswerSharing

sharing = AnswerSharing(
    whatsapp_client=client,
    media_handler=media_handler,
    templates=templates,
)

# Share answer as text
await sharing.share_text_answer(
    to="patient_number",
    answer=medical_answer,
    include_sources=True,
)

# Share as PDF
await sharing.share_pdf_answer(
    to="patient_number",
    answer=medical_answer,
    doctor_name="Dr. Smith",
)

# Share with QR code for app download
await sharing.share_with_qr_code(
    to="patient_number",
    answer=medical_answer,
)
```

### Group Management

```python
from src.whatsapp import GroupManager

group_manager = GroupManager(whatsapp_client=client)

# Register group
group = group_manager.create_group(
    group_id="group_123",
    name="Cardiology Team",
    created_by="919876543210",
)

# Add members
group_manager.add_member("group_123", "919876543211", is_admin=True)

# Broadcast to group
await group_manager.broadcast_to_group(
    group_id="group_123",
    message="Team meeting at 3 PM",
    sender_id="919876543210",
)

# Share query with team
await group_manager.send_query_to_team(
    group_id="group_123",
    query="What's the best antibiotic for UTI?",
    answer="First-line treatment is...",
    sender_id="919876543210",
)
```

## API Endpoints

### Webhook Endpoints

- `GET /api/whatsapp/webhook` - Verify webhook subscription
- `POST /api/whatsapp/webhook` - Receive incoming messages

### Account Management

- `POST /api/whatsapp/link` - Link WhatsApp account (requires 6-digit code)
- `DELETE /api/whatsapp/unlink` - Unlink WhatsApp account
- `GET /api/whatsapp/status` - Get link status

### Messaging

- `POST /api/whatsapp/send` - Send message (admin only)
- `GET /api/whatsapp/history` - Get message history

### Administration

- `GET /api/whatsapp/stats` - Get statistics (admin only)
- `POST /api/whatsapp/notify` - Send notification (admin only)
- `POST /api/whatsapp/broadcast` - Broadcast message (admin only)

### Testing (Development Only)

- `POST /api/whatsapp/test/message` - Send test message
- `GET /api/whatsapp/test/template` - Test message templates

## Sample Conversations

### Medical Query

```
User: What's the dose of amoxicillin for a child?

Dora: For pediatric amoxicillin dosing:
• Age 3-12: 25-50mg/kg/day in 3 divided doses
• Max: 500mg per dose

For a specific calculation, reply with the child's weight in kg.

User: 15kg

Dora: For a 15kg child:
📋 Amoxicillin 375-750mg/day
💊 125-250mg every 8 hours
📅 Duration: As per indication (typically 5-7 days)

[Calculate Again] [Drug Info] [Share with Patient]
```

### Drug Interaction Check

```
User: Check clopidogrel and omeprazole

Dora: 💊 Drug Interaction Check
Drugs: clopidogrel & omeprazole

⚠️ 1 Interaction(s) Found

🟡 1. clopidogrel ↔ omeprazole
Severity: MODERATE

Omeprazole may reduce the effectiveness of clopidogrel...

Management: Consider alternative PPI (e.g., pantoprazole)...
```

### Voice Note Flow

```
User: [Voice note: "Check interaction between clopidogrel and omeprazole"]

Dora: I heard: "Check interaction between clopidogrel and omeprazole"

Let me find the answer...

[Text response with interaction details]

[Optional audio response if voice_responses enabled]
```

## Web Integration

### Settings Page

Located at `/web/app/settings/whatsapp/page.tsx`

Features:
- Link/unlink WhatsApp account
- QR code for quick linking
- View connection status
- Manage preferences
- View features

### Usage

```typescript
import WhatsAppSettingsPage from './settings/whatsapp/page';

// In your settings navigation
<Link href="/settings/whatsapp">WhatsApp</Link>
```

## Mobile Integration

### Flutter/Dart Screen

Located at `/mobile/lib/screens/whatsapp_link_screen.dart`

Features:
- Account linking UI
- QR code display
- Preferences management
- Status display

### Usage

```dart
import 'package:dora/screens/whatsapp_link_screen.dart';

// Navigate to WhatsApp settings
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => const WhatsAppLinkScreen(),
  ),
);
```

### Service

```dart
import 'package:dora/services/whatsapp_service.dart';

final service = WhatsAppService();
service.setToken(authToken);

// Link account
final result = await service.linkAccount(code);

// Get status
final status = await service.getLinkStatus();
```

## Message Templates

Located in `templates.py`, provides pre-formatted messages:

- Welcome message
- Help text
- Query responses (concise, detailed, patient-friendly)
- Drug interaction results
- Calculator outputs
- Error messages
- Linking instructions
- Notifications

## Rate Limiting

The client includes built-in rate limiting:

- Default: 80 messages/second (WhatsApp Cloud API limit)
- Configurable via `RateLimiter` class
- Automatic request queuing

## Error Handling

All handlers include comprehensive error handling:

```python
try:
    await service.process_message(message)
except Exception as e:
    logger.error(f"Error processing message: {e}")
    await client.send_text(
        to=message.from_number,
        text="Sorry, an error occurred. Please try again.",
    )
```

## Security Considerations

1. **Webhook Verification**: All webhooks are signature-verified
2. **PHI Handling**: No patient data stored in WhatsApp messages
3. **HIPAA Compliance**: Draft-mode AI outputs require confirmation
4. **Rate Limiting**: Prevents API abuse
5. **Token Security**: Access tokens stored securely in environment

## Testing

### Unit Tests

```bash
pytest tests/test_whatsapp/
```

### Manual Testing

Use the test endpoints:

```bash
# Send test message
curl -X POST http://localhost:8000/api/whatsapp/test/message \
  -H "Content-Type: application/json" \
  -d '{"to": "919876543210", "message": "Test"}'

# View templates
curl http://localhost:8000/api/whatsapp/test/template
```

## Monitoring

### Statistics

```python
stats = service.get_stats()
# Returns:
# {
#   "whatsapp": {...},
#   "users": {
#     "total_users": 100,
#     "linked_users": 50,
#     "active_conversations": 10,
#     ...
#   },
#   "handlers": {...}
# }
```

### Logging

All operations are logged:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('src.whatsapp')
```

## Troubleshooting

### Webhook not receiving messages

1. Check webhook URL is accessible publicly
2. Verify webhook signature verification
3. Check Meta webhook subscription status
4. Review webhook logs

### Message sending fails

1. Verify access token is valid
2. Check phone number ID is correct
3. Ensure recipient number is in correct format (no + prefix)
4. Check rate limits

### Voice notes not transcribing

1. Ensure Whisper model is installed
2. Check audio format is supported
3. Verify media download is working

## Dependencies

```bash
# Python
pip install httpx  # For async HTTP (recommended)
pip install whisper  # For voice transcription
pip install piper-tts  # For text-to-speech (optional)
pip install reportlab  # For PDF generation
pip install qrcode  # For QR code generation

# Optional: Twilio (if not using Meta Cloud API)
pip install twilio
```

## Contributing

When adding new features:

1. Add models to `models.py`
2. Create handler in `handlers.py`
3. Add templates to `templates.py`
4. Update service in `service.py`
5. Add API endpoints to `api/whatsapp.py`
6. Update this README

## License

This integration is part of the Dora medical knowledge platform.

## Support

For issues or questions:
- GitHub: https://github.com/drshailesh88/Dora
- Email: support@docassist.in

---

**Last Updated**: January 2026
**Version**: 1.0.0
**Status**: Production Ready
