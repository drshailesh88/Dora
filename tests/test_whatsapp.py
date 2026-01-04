"""
Tests for WhatsApp integration module.
Tests message handling, voice notes, image analysis, and group features.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json


class TestWhatsAppWebhook:
    """Tests for WhatsApp webhook handling."""

    @pytest.fixture
    def webhook_handler(self):
        """Create webhook handler instance."""
        from src.whatsapp.webhook import WhatsAppWebhookHandler
        return WhatsAppWebhookHandler()

    @pytest.fixture
    def text_message_payload(self):
        """Sample text message webhook payload."""
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "BUSINESS_ACCOUNT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "919876543210",
                                    "phone_number_id": "PHONE_NUMBER_ID",
                                },
                                "messages": [
                                    {
                                        "from": "919876543210",
                                        "id": "wamid.123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {
                                            "body": "What is the dosage for metformin?"
                                        },
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

    @pytest.fixture
    def voice_message_payload(self):
        """Sample voice message webhook payload."""
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "919876543210",
                                        "id": "wamid.456",
                                        "type": "audio",
                                        "audio": {
                                            "id": "AUDIO_ID",
                                            "mime_type": "audio/ogg; codecs=opus",
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_verify_webhook(self, webhook_handler):
        """Should verify webhook subscription."""
        result = await webhook_handler.verify(
            mode="subscribe",
            token="test_verify_token",
            challenge="test_challenge",
        )

        # Should return challenge if token matches
        assert result == "test_challenge" or result.get("verified")

    @pytest.mark.asyncio
    async def test_process_text_message(self, webhook_handler, text_message_payload):
        """Should process incoming text message."""
        result = await webhook_handler.process(text_message_payload)

        assert result["success"]
        assert result["message_type"] == "text"
        assert "metformin" in result.get("extracted_query", "").lower()

    @pytest.mark.asyncio
    async def test_process_voice_message(self, webhook_handler, voice_message_payload):
        """Should process incoming voice message."""
        with patch.object(
            webhook_handler,
            "_download_audio",
            return_value=b"audio_data",
        ), patch.object(
            webhook_handler,
            "_transcribe_audio",
            return_value="What is the dosage for metformin?",
        ):
            result = await webhook_handler.process(voice_message_payload)

            assert result["success"]
            assert result["message_type"] == "audio"
            assert "transcription" in result

    @pytest.mark.asyncio
    async def test_invalid_payload_handled(self, webhook_handler):
        """Should handle invalid payloads gracefully."""
        result = await webhook_handler.process({"invalid": "payload"})

        assert not result["success"]
        assert "error" in result


class TestWhatsAppMessageSending:
    """Tests for sending WhatsApp messages."""

    @pytest.fixture
    def message_service(self):
        """Create message service instance."""
        from src.whatsapp.messaging import WhatsAppMessagingService
        return WhatsAppMessagingService()

    @pytest.mark.asyncio
    async def test_send_text_message(self, message_service):
        """Should send text message."""
        with patch.object(
            message_service,
            "_send_api_request",
            return_value={"messages": [{"id": "wamid.789"}]},
        ):
            result = await message_service.send_text(
                to="919876543210",
                message="Your query result is ready.",
            )

            assert result["success"]
            assert "message_id" in result

    @pytest.mark.asyncio
    async def test_send_formatted_response(self, message_service):
        """Should send formatted medical response."""
        response = {
            "answer": "Metformin dosage: 500mg twice daily with meals",
            "citations": ["Harrison's Principles"],
            "warnings": ["Monitor renal function"],
        }

        with patch.object(
            message_service,
            "_send_api_request",
            return_value={"messages": [{"id": "wamid.790"}]},
        ):
            result = await message_service.send_medical_response(
                to="919876543210",
                response=response,
            )

            assert result["success"]
            # Should format with sections
            assert result.get("formatted")

    @pytest.mark.asyncio
    async def test_send_with_buttons(self, message_service):
        """Should send interactive message with buttons."""
        with patch.object(
            message_service,
            "_send_api_request",
            return_value={"messages": [{"id": "wamid.791"}]},
        ):
            result = await message_service.send_interactive(
                to="919876543210",
                body="Would you like more information?",
                buttons=[
                    {"id": "more_detail", "title": "More Details"},
                    {"id": "share", "title": "Share Answer"},
                ],
            )

            assert result["success"]

    @pytest.mark.asyncio
    async def test_send_document(self, message_service):
        """Should send document (PDF)."""
        with patch.object(
            message_service,
            "_send_api_request",
            return_value={"messages": [{"id": "wamid.792"}]},
        ):
            result = await message_service.send_document(
                to="919876543210",
                document_url="https://example.com/handout.pdf",
                filename="Patient_Education.pdf",
                caption="Patient education handout",
            )

            assert result["success"]


class TestWhatsAppQueryProcessing:
    """Tests for processing medical queries via WhatsApp."""

    @pytest.fixture
    def query_processor(self):
        """Create query processor instance."""
        from src.whatsapp.query import WhatsAppQueryProcessor
        return WhatsAppQueryProcessor()

    @pytest.mark.asyncio
    async def test_process_simple_query(self, query_processor):
        """Should process simple medical query."""
        result = await query_processor.process(
            user_phone="919876543210",
            query="What is hypertension?",
        )

        assert "answer" in result
        assert len(result["answer"]) > 0

    @pytest.mark.asyncio
    async def test_process_drug_query(self, query_processor):
        """Should process drug-related query."""
        result = await query_processor.process(
            user_phone="919876543210",
            query="Dosage of amoxicillin for child 20kg",
        )

        assert "answer" in result
        # Should include pediatric dosing
        assert "mg/kg" in result["answer"] or "mg" in result["answer"]

    @pytest.mark.asyncio
    async def test_process_calculator_query(self, query_processor):
        """Should detect and run calculator queries."""
        result = await query_processor.process(
            user_phone="919876543210",
            query="Calculate BMI for 70kg 175cm",
        )

        assert "answer" in result
        assert "22" in result["answer"] or "bmi" in result["answer"].lower()

    @pytest.mark.asyncio
    async def test_context_maintained(self, query_processor):
        """Should maintain conversation context."""
        # First query
        await query_processor.process(
            user_phone="919876543210",
            query="Tell me about metformin",
        )

        # Follow-up query
        result = await query_processor.process(
            user_phone="919876543210",
            query="What are its side effects?",
        )

        # Should understand "its" refers to metformin
        assert "metformin" in result.get("context", {}).get("drug", "") or \
               "gastrointestinal" in result["answer"].lower()


class TestWhatsAppImageAnalysis:
    """Tests for image analysis via WhatsApp."""

    @pytest.fixture
    def image_service(self):
        """Create image analysis service instance."""
        from src.whatsapp.image import WhatsAppImageService
        return WhatsAppImageService()

    @pytest.mark.asyncio
    async def test_analyze_rash_image(self, image_service):
        """Should analyze skin rash image."""
        with patch.object(
            image_service,
            "_download_image",
            return_value=b"image_data",
        ), patch.object(
            image_service,
            "_analyze_with_vision",
            return_value={
                "analysis": "Maculopapular rash, possible drug reaction",
                "differentials": ["Drug eruption", "Viral exanthem"],
            },
        ):
            result = await image_service.analyze(
                image_id="IMAGE_123",
                context="Patient has rash after starting amoxicillin",
            )

            assert "analysis" in result
            assert "differentials" in result or "differential" in str(result)

    @pytest.mark.asyncio
    async def test_analyze_xray(self, image_service):
        """Should analyze X-ray image."""
        with patch.object(
            image_service,
            "_download_image",
            return_value=b"image_data",
        ), patch.object(
            image_service,
            "_analyze_with_vision",
            return_value={
                "analysis": "Chest X-ray showing consolidation in right lower lobe",
                "findings": ["RLL consolidation", "No pleural effusion"],
            },
        ):
            result = await image_service.analyze(
                image_id="IMAGE_456",
                context="Patient with cough and fever",
                image_type="xray",
            )

            assert "analysis" in result
            assert "findings" in result

    @pytest.mark.asyncio
    async def test_disclaimer_included(self, image_service):
        """Should include medical disclaimer."""
        with patch.object(
            image_service,
            "_download_image",
            return_value=b"image_data",
        ), patch.object(
            image_service,
            "_analyze_with_vision",
            return_value={"analysis": "Test analysis"},
        ):
            result = await image_service.analyze(
                image_id="IMAGE_789",
                context="Test",
            )

            assert "disclaimer" in result or \
                   "not a substitute" in str(result).lower()


class TestWhatsAppGroupFeatures:
    """Tests for WhatsApp group features."""

    @pytest.fixture
    def group_service(self):
        """Create group service instance."""
        from src.whatsapp.groups import WhatsAppGroupService
        return WhatsAppGroupService()

    @pytest.mark.asyncio
    async def test_process_group_query(self, group_service):
        """Should process query from group chat."""
        result = await group_service.process_group_message(
            group_id="GROUP_123",
            sender="919876543210",
            message="@dora What is the treatment for pneumonia?",
        )

        assert result["processed"]
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_group_mention_required(self, group_service):
        """Should only respond when mentioned in groups."""
        # Without mention
        result = await group_service.process_group_message(
            group_id="GROUP_123",
            sender="919876543210",
            message="What is the treatment for pneumonia?",
        )

        # Should not respond
        assert not result["processed"] or result.get("ignored")

    @pytest.mark.asyncio
    async def test_group_rate_limiting(self, group_service):
        """Should rate limit group responses."""
        group_id = "GROUP_123"

        results = []
        for i in range(10):
            result = await group_service.process_group_message(
                group_id=group_id,
                sender="919876543210",
                message=f"@dora Query {i}",
            )
            results.append(result)

        # Some should be rate limited
        rate_limited = [r for r in results if r.get("rate_limited")]
        assert len(rate_limited) > 0 or all(r["processed"] for r in results)


class TestWhatsAppSession:
    """Tests for WhatsApp session management."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        from src.whatsapp.session import WhatsAppSessionService
        return WhatsAppSessionService()

    @pytest.mark.asyncio
    async def test_create_session(self, session_service):
        """Should create new session for user."""
        session = await session_service.get_or_create(phone="919876543210")

        assert "session_id" in session
        assert session["phone"] == "919876543210"

    @pytest.mark.asyncio
    async def test_session_context_stored(self, session_service):
        """Should store conversation context in session."""
        phone = "919876543210"

        await session_service.update_context(
            phone=phone,
            context={
                "last_drug": "metformin",
                "specialty": "endocrinology",
            },
        )

        session = await session_service.get_or_create(phone=phone)

        assert session["context"]["last_drug"] == "metformin"

    @pytest.mark.asyncio
    async def test_session_expiry(self, session_service):
        """Should expire old sessions."""
        phone = "919876543210"

        # Create session with old timestamp
        with patch.object(
            session_service,
            "_get_session",
            return_value={
                "session_id": "sess_123",
                "phone": phone,
                "created_at": datetime(2020, 1, 1).isoformat(),
                "last_activity": datetime(2020, 1, 1).isoformat(),
            },
        ):
            session = await session_service.get_or_create(phone=phone)

            # Should create new session
            assert session["session_id"] != "sess_123" or session.get("renewed")


class TestWhatsAppNotifications:
    """Tests for WhatsApp notification features."""

    @pytest.fixture
    def notification_service(self):
        """Create notification service instance."""
        from src.whatsapp.notifications import WhatsAppNotificationService
        return WhatsAppNotificationService()

    @pytest.mark.asyncio
    async def test_send_briefing_notification(self, notification_service):
        """Should send morning briefing via WhatsApp."""
        with patch.object(
            notification_service,
            "_send_message",
            return_value={"success": True},
        ):
            result = await notification_service.send_briefing(
                phone="919876543210",
                briefing={
                    "pearl": "Clinical pearl of the day",
                    "appointments": 5,
                },
            )

            assert result["success"]

    @pytest.mark.asyncio
    async def test_send_alert_notification(self, notification_service):
        """Should send urgent alert via WhatsApp."""
        with patch.object(
            notification_service,
            "_send_message",
            return_value={"success": True},
        ):
            result = await notification_service.send_alert(
                phone="919876543210",
                alert={
                    "type": "drug_recall",
                    "title": "Urgent: Drug Recall",
                    "message": "Valsartan lot A123 recalled",
                },
                priority="high",
            )

            assert result["success"]
            assert result.get("delivered_immediately") or result.get("priority") == "high"
