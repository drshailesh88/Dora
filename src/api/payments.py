"""
Payment API Endpoints

REST API for payment operations.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from ..auth import User, get_current_user_required
from ..payments import PaymentService
from ..payments.models import BillingCycle
from ..payments.service import get_payment_service


router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


# Request/Response models
class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"  # monthly, quarterly, yearly
    with_trial: bool = False


class SubscriptionResponse(BaseModel):
    id: str
    plan_id: str
    billing_cycle: str
    status: str
    amount: int
    currency: str = "INR"
    started_at: Optional[str] = None
    current_period_end: Optional[str] = None
    next_billing_date: Optional[str] = None
    is_trial: bool = False
    checkout_url: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class WebhookRequest(BaseModel):
    event: str
    payload: dict


class PlanResponse(BaseModel):
    id: str
    name: str
    description: str
    price_monthly: int
    price_quarterly: int
    price_yearly: int
    currency: str
    features: dict


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    description: str
    subtotal: int
    tax_amount: int
    total: int
    currency: str
    is_paid: bool
    paid_at: Optional[str] = None
    created_at: str


# Endpoints
@router.get("/plans")
async def list_plans():
    """
    Get all available subscription plans.
    """
    service = get_payment_service()
    plans = service.get_plans()

    return {
        "plans": [p.to_dict() for p in plans],
    }


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    """
    Get a specific plan.
    """
    service = get_payment_service()
    plan = service.get_plan(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return plan.to_dict()


@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user: User = Depends(get_current_user_required),
):
    """
    Create a new subscription.

    Returns checkout URL if payment is required.
    """
    service = get_payment_service()

    try:
        billing_cycle = BillingCycle(request.billing_cycle)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid billing cycle: {request.billing_cycle}"
        )

    result = service.create_subscription(
        user_id=user.id,
        plan_id=request.plan_id,
        billing_cycle=billing_cycle,
        customer_email=user.email,
        organization_id=user.organization_id,
        with_trial=request.with_trial,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    sub = result.subscription
    return SubscriptionResponse(
        id=sub.id,
        plan_id=sub.plan_id,
        billing_cycle=sub.billing_cycle.value,
        status=sub.status.value,
        amount=sub.amount,
        started_at=sub.started_at.isoformat() if sub.started_at else None,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        next_billing_date=sub.next_billing_date.isoformat() if sub.next_billing_date else None,
        is_trial=sub.is_trial,
        checkout_url=result.checkout_url,
    )


@router.get("/subscriptions/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    user: User = Depends(get_current_user_required),
):
    """
    Get user's current subscription.
    """
    service = get_payment_service()
    sub = service.get_user_subscription(user.id)

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")

    return SubscriptionResponse(
        id=sub.id,
        plan_id=sub.plan_id,
        billing_cycle=sub.billing_cycle.value,
        status=sub.status.value,
        amount=sub.amount,
        started_at=sub.started_at.isoformat() if sub.started_at else None,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        next_billing_date=sub.next_billing_date.isoformat() if sub.next_billing_date else None,
        is_trial=sub.is_trial,
    )


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = True,
    user: User = Depends(get_current_user_required),
):
    """
    Cancel a subscription.
    """
    service = get_payment_service()

    # Verify ownership
    sub = service.get_subscription(subscription_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    result = service.cancel_subscription(
        subscription_id=subscription_id,
        at_period_end=at_period_end,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "success": True,
        "message": "Subscription cancelled" + (" at period end" if at_period_end else ""),
    }


@router.post("/subscriptions/{subscription_id}/change-plan")
async def change_subscription_plan(
    subscription_id: str,
    plan_id: str,
    billing_cycle: Optional[str] = None,
    at_period_end: bool = True,
    user: User = Depends(get_current_user_required),
):
    """
    Change subscription plan.
    """
    service = get_payment_service()

    # Verify ownership
    sub = service.get_subscription(subscription_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    new_cycle = None
    if billing_cycle:
        try:
            new_cycle = BillingCycle(billing_cycle)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid billing cycle")

    result = service.change_plan(
        subscription_id=subscription_id,
        new_plan_id=plan_id,
        new_billing_cycle=new_cycle,
        at_period_end=at_period_end,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "success": True,
        "subscription": result.subscription.to_dict(),
    }


@router.post("/verify")
async def verify_payment(
    request: PaymentVerifyRequest,
    user: User = Depends(get_current_user_required),
):
    """
    Verify payment after Razorpay checkout.
    """
    service = get_payment_service()

    result = service.verify_payment(
        order_id=request.order_id,
        payment_id=request.payment_id,
        signature=request.signature,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "success": True,
        "payment": result.payment.to_dict(),
    }


@router.get("/history")
async def get_payment_history(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user_required),
):
    """
    Get user's payment history.
    """
    service = get_payment_service()
    payments = service.get_user_payments(user.id, limit, offset)

    return {
        "payments": [p.to_dict() for p in payments],
        "limit": limit,
        "offset": offset,
    }


@router.get("/invoices")
async def get_invoices(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user_required),
):
    """
    Get user's invoices.
    """
    service = get_payment_service()
    invoices = service.get_user_invoices(user.id, limit, offset)

    return {
        "invoices": [inv.to_dict() for inv in invoices],
        "limit": limit,
        "offset": offset,
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: User = Depends(get_current_user_required),
):
    """
    Get a specific invoice.
    """
    service = get_payment_service()
    invoice = service.get_invoice(invoice_id)

    if not invoice or invoice.user_id != user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice.to_dict()


# Webhook endpoint (no auth - verified by signature)
@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle Razorpay webhooks.
    """
    service = get_payment_service()

    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify signature
    if not service.razorpay.verify_webhook_signature(body.decode(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    import json
    data = json.loads(body)
    event_type = data.get("event", "")
    payload = data.get("payload", {})

    # Handle event
    success = service.handle_webhook(event_type, payload)

    if not success:
        raise HTTPException(status_code=500, detail="Webhook processing failed")

    return {"status": "ok"}


# Razorpay checkout configuration
@router.get("/config")
async def get_payment_config(
    user: User = Depends(get_current_user_required),
):
    """
    Get Razorpay configuration for frontend checkout.
    """
    service = get_payment_service()

    return {
        "key_id": service.razorpay.config.key_id,
        "currency": "INR",
        "name": "DocAssist Dora",
        "description": "Medical Knowledge Platform",
        "prefill": {
            "email": user.email,
            "name": user.name,
        },
        "theme": {
            "color": "#0066CC",
        },
    }
