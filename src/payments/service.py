"""
Payment Service

Central service for payment operations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .models import (
    PaymentPlan, Subscription, Payment, Invoice,
    PaymentStatus, SubscriptionStatus, BillingCycle, PLANS
)
from .razorpay_client import RazorpayClient, get_razorpay_client
from .storage import PaymentStorage, get_payment_storage


@dataclass
class SubscriptionResult:
    """Result of subscription operation."""
    success: bool
    subscription: Optional[Subscription] = None
    checkout_url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PaymentResult:
    """Result of payment operation."""
    success: bool
    payment: Optional[Payment] = None
    order_id: Optional[str] = None
    error: Optional[str] = None


class PaymentService:
    """
    Central payment service.

    Handles:
    - Subscription creation and management
    - Payment processing
    - Invoice generation
    - Webhook handling
    """

    def __init__(
        self,
        storage: Optional[PaymentStorage] = None,
        razorpay: Optional[RazorpayClient] = None,
    ):
        self.storage = storage or get_payment_storage()
        self.razorpay = razorpay or get_razorpay_client()

    # Plan operations
    def get_plans(self) -> list[PaymentPlan]:
        """Get all available plans."""
        return list(PLANS.values())

    def get_plan(self, plan_id: str) -> Optional[PaymentPlan]:
        """Get a plan by ID."""
        return PLANS.get(plan_id)

    # Subscription operations
    def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        customer_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        with_trial: bool = False,
    ) -> SubscriptionResult:
        """
        Create a new subscription.

        If Razorpay is configured, creates a Razorpay subscription.
        Otherwise, creates a local subscription (for testing).
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return SubscriptionResult(success=False, error="Invalid plan ID")

        # Check for existing active subscription
        existing = self.storage.get_user_subscription(user_id)
        if existing and existing.status == SubscriptionStatus.ACTIVE:
            return SubscriptionResult(
                success=False,
                error="User already has an active subscription",
                subscription=existing,
            )

        # Get price for billing cycle
        amount = plan.get_price(billing_cycle)

        # Create subscription record
        subscription = Subscription(
            user_id=user_id,
            organization_id=organization_id,
            plan_id=plan_id,
            billing_cycle=billing_cycle,
            amount=amount,
            status=SubscriptionStatus.PENDING,
        )

        if with_trial:
            subscription.is_trial = True
            subscription.trial_ends_at = datetime.utcnow() + timedelta(days=14)

        # Try to create Razorpay subscription
        razorpay_plan_id = plan.get_razorpay_plan_id(billing_cycle)
        if razorpay_plan_id and self.razorpay.config.key_id:
            rp_sub = self.razorpay.create_subscription(
                plan_id=razorpay_plan_id,
                customer_email=customer_email,
                total_count=12 if billing_cycle == BillingCycle.MONTHLY else 4 if billing_cycle == BillingCycle.QUARTERLY else 1,
                notes={"user_id": user_id, "plan_id": plan_id},
            )

            if rp_sub:
                subscription.razorpay_subscription_id = rp_sub.get("id")
                subscription.razorpay_customer_id = rp_sub.get("customer_id")

                # Save and return with checkout URL
                self.storage.create_subscription(subscription)

                short_url = rp_sub.get("short_url")
                return SubscriptionResult(
                    success=True,
                    subscription=subscription,
                    checkout_url=short_url,
                )
            else:
                return SubscriptionResult(
                    success=False,
                    error="Failed to create Razorpay subscription"
                )
        else:
            # No Razorpay - activate immediately (for testing/free plan)
            if plan_id == "free":
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.started_at = datetime.utcnow()
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=365)

            self.storage.create_subscription(subscription)

            return SubscriptionResult(
                success=True,
                subscription=subscription,
            )

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID."""
        return self.storage.get_subscription(subscription_id)

    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self.storage.get_user_subscription(user_id)

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> SubscriptionResult:
        """
        Cancel a subscription.

        If at_period_end is True, cancels at end of billing period.
        Otherwise, cancels immediately.
        """
        subscription = self.storage.get_subscription(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING]:
            return SubscriptionResult(
                success=False,
                error=f"Cannot cancel subscription with status: {subscription.status.value}"
            )

        # Cancel in Razorpay
        if subscription.razorpay_subscription_id:
            result = self.razorpay.cancel_subscription(
                subscription.razorpay_subscription_id,
                cancel_at_cycle_end=at_period_end,
            )
            if not result:
                return SubscriptionResult(
                    success=False,
                    error="Failed to cancel in Razorpay"
                )

        # Update local record
        subscription.cancelled_at = datetime.utcnow()
        if not at_period_end:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.ended_at = datetime.utcnow()
        else:
            # Will be cancelled at period end
            subscription.status = SubscriptionStatus.ACTIVE

        self.storage.update_subscription(subscription)

        return SubscriptionResult(success=True, subscription=subscription)

    def change_plan(
        self,
        subscription_id: str,
        new_plan_id: str,
        new_billing_cycle: Optional[BillingCycle] = None,
        at_period_end: bool = True,
    ) -> SubscriptionResult:
        """
        Change subscription plan.
        """
        subscription = self.storage.get_subscription(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        new_plan = self.get_plan(new_plan_id)
        if not new_plan:
            return SubscriptionResult(success=False, error="Invalid plan ID")

        billing_cycle = new_billing_cycle or subscription.billing_cycle

        # Update in Razorpay
        if subscription.razorpay_subscription_id:
            new_razorpay_plan = new_plan.get_razorpay_plan_id(billing_cycle)
            if new_razorpay_plan:
                result = self.razorpay.update_subscription(
                    subscription.razorpay_subscription_id,
                    plan_id=new_razorpay_plan,
                    schedule_change_at="cycle_end" if at_period_end else "now",
                )
                if not result:
                    return SubscriptionResult(
                        success=False,
                        error="Failed to update in Razorpay"
                    )

        # Update local record
        if not at_period_end:
            subscription.plan_id = new_plan_id
            subscription.billing_cycle = billing_cycle
            subscription.amount = new_plan.get_price(billing_cycle)

        self.storage.update_subscription(subscription)

        return SubscriptionResult(success=True, subscription=subscription)

    # Payment operations
    def create_payment(
        self,
        user_id: str,
        amount: int,
        subscription_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PaymentResult:
        """
        Create a payment order.

        Returns order ID for frontend checkout.
        """
        # Create Razorpay order
        order = self.razorpay.create_order(
            amount=amount,
            notes={"user_id": user_id, "subscription_id": subscription_id},
        )

        if not order:
            return PaymentResult(success=False, error="Failed to create order")

        # Create payment record
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            razorpay_order_id=order.get("id"),
            status=PaymentStatus.PENDING,
        )
        self.storage.create_payment(payment)

        return PaymentResult(
            success=True,
            payment=payment,
            order_id=order.get("id"),
        )

    def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> PaymentResult:
        """
        Verify payment after checkout.
        """
        # Verify signature
        if not self.razorpay.verify_payment_signature(order_id, payment_id, signature):
            return PaymentResult(success=False, error="Invalid signature")

        # Get payment by order ID using proper lookup
        payment = self.storage.get_payment_by_order_id(order_id)

        if not payment:
            return PaymentResult(success=False, error="Payment not found")

        # Update payment
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()

        # Get payment method from Razorpay
        rp_payment = self.razorpay.get_payment(payment_id)
        if rp_payment:
            payment.method = rp_payment.get("method")

        self.storage.update_payment(payment)

        # If subscription payment, activate subscription
        if payment.subscription_id:
            subscription = self.storage.get_subscription(payment.subscription_id)
            if subscription and subscription.status == SubscriptionStatus.PENDING:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.started_at = datetime.utcnow()
                subscription.current_period_start = datetime.utcnow()

                # Calculate period end based on billing cycle
                if subscription.billing_cycle == BillingCycle.MONTHLY:
                    subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                elif subscription.billing_cycle == BillingCycle.QUARTERLY:
                    subscription.current_period_end = datetime.utcnow() + timedelta(days=90)
                else:
                    subscription.current_period_end = datetime.utcnow() + timedelta(days=365)

                subscription.next_billing_date = subscription.current_period_end
                self.storage.update_subscription(subscription)

        # Generate invoice
        self._generate_invoice_for_payment(payment)

        return PaymentResult(success=True, payment=payment)

    def get_user_payments(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        """Get user's payment history."""
        return self.storage.get_user_payments(user_id, limit, offset)

    # Invoice operations
    def get_user_invoices(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Invoice]:
        """Get user's invoices."""
        return self.storage.get_user_invoices(user_id, limit, offset)

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        return self.storage.get_invoice(invoice_id)

    def _generate_invoice_for_payment(
        self,
        payment: Payment,
    ) -> Invoice:
        """Generate invoice for a completed payment."""
        # Get user info (would come from auth service in real implementation)
        # For now, create with basic info

        subscription = None
        plan = None
        if payment.subscription_id:
            subscription = self.storage.get_subscription(payment.subscription_id)
            if subscription:
                plan = self.get_plan(subscription.plan_id)

        description = f"Dora {plan.name if plan else 'Subscription'}"
        if subscription:
            description += f" - {subscription.billing_cycle.value.title()}"

        invoice = Invoice(
            user_id=payment.user_id,
            subscription_id=payment.subscription_id,
            payment_id=payment.id,
            invoice_number=self.storage.generate_invoice_number(),
            description=description,
            subtotal=payment.amount,
            currency=payment.currency,
            is_paid=True,
            paid_at=payment.completed_at,
        )

        # Calculate GST (18%)
        invoice.calculate_tax(0.18)

        if subscription:
            invoice.period_start = subscription.current_period_start
            invoice.period_end = subscription.current_period_end

        self.storage.create_invoice(invoice)
        return invoice

    # Webhook handling
    def handle_webhook(self, event_type: str, payload: dict) -> bool:
        """
        Handle Razorpay webhook events.

        Common events:
        - subscription.authenticated
        - subscription.activated
        - subscription.charged
        - subscription.cancelled
        - subscription.halted
        - payment.captured
        - payment.failed
        """
        try:
            if event_type == "subscription.authenticated":
                return self._handle_subscription_authenticated(payload)
            elif event_type == "subscription.activated":
                return self._handle_subscription_activated(payload)
            elif event_type == "subscription.charged":
                return self._handle_subscription_charged(payload)
            elif event_type == "subscription.cancelled":
                return self._handle_subscription_cancelled(payload)
            elif event_type == "subscription.halted":
                return self._handle_subscription_halted(payload)
            elif event_type == "payment.captured":
                return self._handle_payment_captured(payload)
            elif event_type == "payment.failed":
                return self._handle_payment_failed(payload)
            else:
                print(f"Unhandled webhook event: {event_type}")
                return True  # Don't retry unknown events

        except Exception as e:
            print(f"Webhook error: {e}")
            return False

    def _handle_subscription_authenticated(self, payload: dict) -> bool:
        """Handle subscription authentication (first charge pending)."""
        rp_sub = payload.get("subscription", {})
        subscription = self.storage.get_subscription_by_razorpay_id(rp_sub.get("id"))
        if subscription:
            subscription.status = SubscriptionStatus.PENDING
            self.storage.update_subscription(subscription)
        return True

    def _handle_subscription_activated(self, payload: dict) -> bool:
        """Handle subscription activation (first charge successful)."""
        rp_sub = payload.get("subscription", {})
        subscription = self.storage.get_subscription_by_razorpay_id(rp_sub.get("id"))
        if subscription:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.started_at = datetime.utcnow()
            subscription.current_period_start = datetime.utcnow()

            # Parse charge_at from Razorpay
            charge_at = rp_sub.get("charge_at")
            if charge_at:
                subscription.next_billing_date = datetime.fromtimestamp(charge_at)
                subscription.current_period_end = subscription.next_billing_date

            self.storage.update_subscription(subscription)
        return True

    def _handle_subscription_charged(self, payload: dict) -> bool:
        """Handle recurring subscription charge."""
        rp_sub = payload.get("subscription", {})
        rp_payment = payload.get("payment", {})

        subscription = self.storage.get_subscription_by_razorpay_id(rp_sub.get("id"))
        if not subscription:
            return True

        # Create payment record
        payment = Payment(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            amount=rp_payment.get("amount", 0),
            currency=rp_payment.get("currency", "INR"),
            status=PaymentStatus.COMPLETED,
            razorpay_payment_id=rp_payment.get("id"),
            method=rp_payment.get("method"),
            completed_at=datetime.utcnow(),
        )
        self.storage.create_payment(payment)

        # Update subscription periods
        subscription.current_period_start = datetime.utcnow()
        charge_at = rp_sub.get("charge_at")
        if charge_at:
            subscription.next_billing_date = datetime.fromtimestamp(charge_at)
            subscription.current_period_end = subscription.next_billing_date
        self.storage.update_subscription(subscription)

        # Generate invoice
        self._generate_invoice_for_payment(payment)

        return True

    def _handle_subscription_cancelled(self, payload: dict) -> bool:
        """Handle subscription cancellation."""
        rp_sub = payload.get("subscription", {})
        subscription = self.storage.get_subscription_by_razorpay_id(rp_sub.get("id"))
        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.ended_at = datetime.utcnow()
            self.storage.update_subscription(subscription)
        return True

    def _handle_subscription_halted(self, payload: dict) -> bool:
        """Handle subscription halt (payment failures)."""
        rp_sub = payload.get("subscription", {})
        subscription = self.storage.get_subscription_by_razorpay_id(rp_sub.get("id"))
        if subscription:
            subscription.status = SubscriptionStatus.HALTED
            self.storage.update_subscription(subscription)
        return True

    def _handle_payment_captured(self, payload: dict) -> bool:
        """Handle one-time payment capture."""
        rp_payment = payload.get("payment", {})
        payment = self.storage.get_payment_by_razorpay_id(rp_payment.get("id"))
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.method = rp_payment.get("method")
            self.storage.update_payment(payment)
        return True

    def _handle_payment_failed(self, payload: dict) -> bool:
        """Handle payment failure."""
        rp_payment = payload.get("payment", {})
        payment = self.storage.get_payment_by_razorpay_id(rp_payment.get("id"))
        if payment:
            payment.status = PaymentStatus.FAILED
            error = rp_payment.get("error", {})
            payment.error_code = error.get("code")
            payment.error_description = error.get("description")
            self.storage.update_payment(payment)
        return True


# Default instance
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """Get the default payment service instance."""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
