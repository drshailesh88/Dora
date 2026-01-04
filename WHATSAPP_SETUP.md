# WhatsApp Integration - Quick Setup Guide

## Prerequisites

1. **Meta Business Account**: Create at https://business.facebook.com
2. **WhatsApp Business App**: Set up WhatsApp Business API
3. **Dora Backend**: Running FastAPI server
4. **Publicly Accessible URL**: For webhook (use ngrok for testing)

## Step-by-Step Setup

### 1. Get WhatsApp Credentials

1. Go to https://developers.facebook.com/apps
2. Create a new app (Business type)
3. Add "WhatsApp" product
4. Navigate to WhatsApp > API Setup
5. Note down:
   - **Access Token** (temporary, replace with permanent token later)
   - **Phone Number ID**
   - **Business Account ID**
6. Go to App Settings > Basic
   - Note down **App Secret**
7. Create a **Verify Token** (any random string, e.g., "dora_webhook_123")

### 2. Configure Environment Variables

Add to `/home/user/Dora/.env`:

```bash
# WhatsApp Cloud API Credentials
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_BUSINESS_ACCOUNT_ID=987654321098765
WHATSAPP_APP_SECRET=abcdef1234567890
WHATSAPP_VERIFY_TOKEN=dora_webhook_123
```

### 3. Install Dependencies

```bash
cd /home/user/Dora
pip install -r requirements-whatsapp.txt
```

### 4. Configure Webhook

#### For Production:

1. Ensure your server is accessible at `https://your-domain.com`
2. In Meta Developer Console > WhatsApp > Configuration
3. Set webhook URL: `https://your-domain.com/api/whatsapp/webhook`
4. Enter your verify token: `dora_webhook_123`
5. Subscribe to fields:
   - `messages`
   - `message_status`

#### For Development (using ngrok):

```bash
# Start ngrok
ngrok http 8000

# Use the ngrok URL
# e.g., https://abc123.ngrok.io/api/whatsapp/webhook
```

### 5. Start the Server

```bash
cd /home/user/Dora
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test the Integration

#### Test Webhook Verification:

```bash
# Should return 200 OK
curl -X GET "http://localhost:8000/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=dora_webhook_123&hub.challenge=test123"
```

#### Send Test Message:

```bash
curl -X POST http://localhost:8000/api/whatsapp/test/message \
  -H "Content-Type: application/json" \
  -d '{
    "to": "919876543210",
    "message": "Hello from Dora! Testing WhatsApp integration."
  }'
```

Replace `919876543210` with your WhatsApp number (country code + number, no + sign).

#### Test via WhatsApp:

1. Message the WhatsApp number you configured
2. Send: `help`
3. You should receive a help message
4. Try: `What is amoxicillin?`

### 7. Link Your Account

#### Via Web App:

1. Go to `http://localhost:3000/settings/whatsapp`
2. Send `link` to the WhatsApp number
3. Enter the 6-digit code you receive
4. Click "Link Account"

#### Via Mobile App:

1. Open the Dora mobile app
2. Go to Settings > WhatsApp
3. Follow the same linking process

### 8. Verify Everything Works

Test these features:

1. **Text Query**: Send a medical question
2. **Voice Note**: Send a voice note with a question
3. **Drug Check**: Send `check aspirin and warfarin`
4. **Calculator**: Send `calculator`
5. **Help**: Send `help`

## Common Issues

### Webhook Not Receiving Messages

**Problem**: Messages sent to WhatsApp number but no response

**Solutions**:
- Check webhook is accessible publicly (test with curl)
- Verify webhook signature verification is working
- Check logs: `tail -f /var/log/dora.log`
- Ensure webhook fields are subscribed in Meta Console
- Verify access token is valid (they expire)

### Messages Not Sending

**Problem**: API returns error when sending

**Solutions**:
- Verify access token is correct and not expired
- Check phone number ID is correct
- Ensure recipient number format is correct (no + prefix)
- Check you're not hitting rate limits (80 msg/sec)
- Verify WhatsApp number is verified in Meta Console

### Voice Notes Not Working

**Problem**: Voice notes not transcribed

**Solutions**:
- Ensure Whisper is installed: `pip install openai-whisper`
- Check media download is working
- Verify audio format is supported (OGG/MP3/M4A)
- Check file size limits (16MB max)

### Link Code Not Working

**Problem**: 6-digit code doesn't work

**Solutions**:
- Codes expire after 15 minutes
- Generate a new code by sending `link` again
- Verify code is exactly 6 digits
- Check conversation manager storage is writable

## Architecture Overview

```
User (WhatsApp)
    ↓
Meta WhatsApp Cloud API
    ↓
Webhook → /api/whatsapp/webhook
    ↓
WebhookHandler (verify signature)
    ↓
WebhookParser (parse message)
    ↓
WhatsAppService (route to handler)
    ↓
├─ TextQueryHandler → RAG Pipeline → Response
├─ VoiceNoteHandler → STT → RAG → TTS → Response
├─ DrugCheckHandler → Drug Checker → Response
├─ ButtonHandler → Route to appropriate handler
└─ ImageHandler → Image Analysis (coming soon)
    ↓
WhatsAppClient (send response)
    ↓
Meta WhatsApp Cloud API
    ↓
User (WhatsApp)
```

## Security Checklist

- [ ] Webhook signature verification enabled
- [ ] Access tokens stored in environment variables (not code)
- [ ] HTTPS enabled for webhook URL
- [ ] Rate limiting configured
- [ ] No PHI stored in logs
- [ ] Conversation data encrypted at rest
- [ ] Regular token rotation
- [ ] Audit logging enabled

## Production Deployment

### 1. Get Permanent Access Token

Temporary tokens expire. Generate a permanent token:

1. Go to Meta Business Manager > System Users
2. Create a system user
3. Assign WhatsApp Business Management permission
4. Generate token (never expires)
5. Update `.env` with new token

### 2. Use Production Database

Update conversation manager to use PostgreSQL instead of JSON files:

```python
# In service.py
conversation_manager = ConversationManager(
    storage_dir=None,  # Will use PostgreSQL
    db_url="postgresql://user:pass@localhost/dora"
)
```

### 3. Enable SSL

Ensure your webhook URL uses HTTPS:

```bash
# With nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/whatsapp/webhook {
        proxy_pass http://localhost:8000;
    }
}
```

### 4. Configure Monitoring

```python
# Add to your monitoring system
from src.whatsapp import WhatsAppService

service = WhatsAppService()
stats = service.get_stats()

# Monitor:
# - Message volume
# - Error rates
# - Response times
# - User engagement
```

### 5. Set Up Message Queue

For high volume, use a message queue:

```python
# With Celery
@celery.task
def process_whatsapp_message(message_data):
    service = WhatsAppService()
    message = WhatsAppMessage.from_dict(message_data)
    await service.process_message(message)

# In webhook handler
@router.post("/webhook")
async def receive_webhook(request: Request):
    # ... parse webhook ...

    # Queue for processing
    process_whatsapp_message.delay(message.to_dict())

    return {"success": True}  # Return immediately
```

## Next Steps

1. **Customize Templates**: Edit `/src/whatsapp/templates.py` for your needs
2. **Add Features**: Implement image analysis, more calculators, etc.
3. **Integrate EMR**: Connect to patient records for personalized responses
4. **Analytics**: Track usage patterns and optimize
5. **Scale**: Add load balancing and caching for high volume

## Support

- **Documentation**: `/src/whatsapp/README.md`
- **Issues**: https://github.com/drshailesh88/Dora/issues
- **Email**: support@docassist.in

## Meta Resources

- [WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)
- [Webhooks Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates)

---

**Version**: 1.0.0
**Last Updated**: January 2026
**Tested On**: Python 3.11+, FastAPI 0.100+
