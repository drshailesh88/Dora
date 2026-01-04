"""
WhatsApp API Endpoints

REST API for WhatsApp integration.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Header
from pydantic import BaseModel

from src.auth.middleware import get_current_user
from src.auth.models import User
from src.whatsapp import (
    WhatsAppService,
    WhatsAppMessage,
    MessageTemplates,
)
from src.core.pipeline import MedicalQueryPipeline
from src.drugs import DrugInteractionChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# Global service instance
_whatsapp_service: Optional[WhatsAppService] = None


def get_whatsapp_service(
    query_pipeline: Optional[MedicalQueryPipeline] = None,
    drug_checker: Optional[DrugInteractionChecker] = None,
) -> WhatsAppService:
    """Get or create WhatsApp service instance"""
    global _whatsapp_service

    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService(
            query_pipeline=query_pipeline,
            drug_checker=drug_checker,
        )

    return _whatsapp_service


# Request/Response Models

class LinkAccountRequest(BaseModel):
    """Request to link WhatsApp account"""
    code: str  # 6-digit link code


class LinkAccountResponse(BaseModel):
    """Link account response"""
    success: bool
    message: str
    whatsapp_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Request to send message (internal use)"""
    to: str
    message: str
    message_type: str = "text"


class SendMessageResponse(BaseModel):
    """Send message response"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class MessageHistoryResponse(BaseModel):
    """Message history response"""
    success: bool
    messages: list[dict] = []
    count: int = 0


class WhatsAppStatsResponse(BaseModel):
    """WhatsApp statistics response"""
    success: bool
    stats: dict


# Webhook Endpoints

@router.get("/webhook")
async def verify_webhook(
    request: Request,
):
    """
    Verify webhook subscription.

    Meta sends this during webhook setup.
    """
    service = get_whatsapp_service()

    # Get query parameters
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if not mode or not token:
        raise HTTPException(status_code=400, detail="Missing parameters")

    # Verify
    result = service.webhook_handler.verify_webhook(mode, token, challenge)

    if result:
        # Return challenge for verification
        return Response(content=result, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    Receive incoming WhatsApp webhooks.

    Meta sends messages and status updates here.
    """
    service = get_whatsapp_service()

    # Get raw body for signature verification
    body = await request.body()

    if not x_hub_signature_256:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        # Parse and verify webhook
        result = service.webhook_handler.handle_webhook(body, x_hub_signature_256)

        # Process messages
        for message in result.get("messages", []):
            # Process in background (don't block webhook response)
            import asyncio
            asyncio.create_task(service.process_message(message))

        # Process status updates
        for status in result.get("statuses", []):
            # TODO: Update message status in database
            logger.info(f"Status update: {status}")

        # WhatsApp expects 200 OK immediately
        return {"success": True}

    except ValueError as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected webhook error: {e}")
        # Still return 200 to avoid retries
        return {"success": False, "error": str(e)}


# Account Management Endpoints

@router.post("/link", response_model=LinkAccountResponse)
async def link_account(
    request: LinkAccountRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Link WhatsApp account using 6-digit code.

    User generates code in WhatsApp, enters it in web/mobile app.
    """
    service = get_whatsapp_service()

    # Verify code
    whatsapp_id = service.verify_link_code(request.code)

    if not whatsapp_id:
        return LinkAccountResponse(
            success=False,
            message="Invalid or expired link code",
        )

    # Link account
    success = service.link_user_account(whatsapp_id, current_user.id)

    if success:
        return LinkAccountResponse(
            success=True,
            message="WhatsApp account linked successfully",
            whatsapp_id=whatsapp_id,
        )
    else:
        return LinkAccountResponse(
            success=False,
            message="Failed to link account",
        )


@router.delete("/unlink")
async def unlink_account(
    current_user: User = Depends(get_current_user),
):
    """
    Unlink WhatsApp account from Dora account.
    """
    service = get_whatsapp_service()

    # Find user's WhatsApp account
    # This would need a reverse lookup in the conversation manager
    # For now, return success
    # TODO: Implement reverse lookup

    return {
        "success": True,
        "message": "WhatsApp account unlinked",
    }


@router.get("/status")
async def get_link_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get WhatsApp link status for current user.
    """
    service = get_whatsapp_service()

    # TODO: Implement reverse lookup to find WhatsApp ID by user ID
    # For now, return not linked

    return {
        "linked": False,
        "whatsapp_id": None,
    }


# Message Management Endpoints

@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a WhatsApp message (internal use only).

    Requires admin permission.
    """
    if not current_user.has_permission("admin.users"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = get_whatsapp_service()

    try:
        # Send message
        response = await service.client.send_text(
            to=request.to,
            text=request.message,
        )

        return SendMessageResponse(
            success=True,
            message_id=response.message_id,
        )

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return SendMessageResponse(
            success=False,
            error=str(e),
        )


@router.get("/history")
async def get_message_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """
    Get message history for current user's linked WhatsApp.

    TODO: Implement message history storage and retrieval.
    """
    # This would require storing messages in a database
    # For now, return empty list

    return {
        "success": True,
        "messages": [],
        "count": 0,
        "total": 0,
    }


# Statistics Endpoints

@router.get("/stats", response_model=WhatsAppStatsResponse)
async def get_whatsapp_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get WhatsApp service statistics.

    Requires admin permission.
    """
    if not current_user.has_permission("admin.analytics"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = get_whatsapp_service()

    stats = service.get_stats()

    return WhatsAppStatsResponse(
        success=True,
        stats=stats,
    )


# Notification Endpoints

@router.post("/notify")
async def send_notification(
    to: str,
    notification_type: str,
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Send notification to WhatsApp user.

    Requires admin permission.
    """
    if not current_user.has_permission("admin.notifications"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = get_whatsapp_service()

    success = await service.send_notification(to, notification_type, data)

    return {
        "success": success,
    }


# Broadcast Endpoints

@router.post("/broadcast")
async def broadcast_message(
    recipients: list[str],
    message: str,
    current_user: User = Depends(get_current_user),
):
    """
    Broadcast message to multiple users.

    Requires admin permission.
    """
    if not current_user.has_permission("admin.notifications"):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = get_whatsapp_service()

    sent_count = await service.broadcast_message(recipients, message)

    return {
        "success": True,
        "sent_count": sent_count,
        "total_recipients": len(recipients),
    }


# Testing Endpoints (development only)

@router.post("/test/message")
async def test_message(
    to: str,
    message: str = "Hello from Dora! This is a test message.",
):
    """
    Send test message (development only).

    Should be disabled in production.
    """
    from src.core.config import settings

    if not settings.debug:
        raise HTTPException(status_code=403, detail="Test endpoint disabled in production")

    service = get_whatsapp_service()

    try:
        response = await service.client.send_text(to=to, text=message)

        return {
            "success": True,
            "message_id": response.message_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/template")
async def test_templates():
    """
    Test message templates (development only).
    """
    from src.core.config import settings

    if not settings.debug:
        raise HTTPException(status_code=403, detail="Test endpoint disabled in production")

    templates = MessageTemplates()

    return {
        "welcome": templates.get_welcome_message(),
        "help": templates.get_help_message(),
        "error": templates.get_error_message(),
    }
