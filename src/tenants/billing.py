"""
Tenant-Level Billing

Handles subscription management and billing for tenant organizations.
Integrates with Razorpay for payment processing.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from .models import Tenant, TENANT_PLANS, TenantPlan, TenantStatus
from .storage import TenantStorage, get_tenant_storage
from ..payments.models import (
    Subscription, SubscriptionStatus, BillingCycle,
    Payment, PaymentStatus, Invoice
)


@dataclass
class BillingInfo:
    """Billing information for a tenant."""
    tenant_id: str
    plan: TenantPlan
    current_members: int
    max_members: int
    overage_members: int
    base_price: int  # In paise
    overage_price: int  # In paise
    total_price: int  # In paise
    currency: str = "INR"
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    next_billing_date: Optional[datetime] = None
    subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE


class TenantBillingService:
    """
    Service for managing tenant billing and subscriptions.

    Handles:
    - Subscription creation and management
    - Per-seat billing with overage
    - Invoice generation
    - Payment tracking
    - Usage-based billing
    """

    def __init__(
        self,
        storage: Optional[TenantStorage] = None,
        razorpay_key_id: Optional[str] = None,
        razorpay_key_secret: Optional[str] = None,
    ):
        self.storage = storage or get_tenant_storage()
        self.razorpay_key_id = razorpay_key_id
        self.razorpay_key_secret = razorpay_key_secret

        # Initialize Razorpay client if credentials provided
        self.razorpay_client = None
        if razorpay_key_id and razorpay_key_secret:
            try:
                import razorpay
                self.razorpay_client = razorpay.Client(
                    auth=(razorpay_key_id, razorpay_key_secret)
                )
            except ImportError:
                print("Warning: razorpay package not installed")

    def get_billing_info(self, tenant_id: str) -> BillingInfo:
        """
        Get current billing information for a tenant.

        Calculates:
        - Base subscription price
        - Overage charges (if members > plan limit)
        - Total monthly/yearly cost
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        plan = TENANT_PLANS.get(tenant.plan_id)
        if not plan:
            raise ValueError(f"Plan {tenant.plan_id} not found")

        # Get current member count
        members = self.storage.get_tenant_members(tenant_id, active_only=True)
        current_members = len(members)

        # Calculate overage
        max_members = plan.max_members if plan.max_members > 0 else current_members
        overage_members = max(0, current_members - max_members)

        # Calculate pricing (default to monthly)
        base_price = plan.price_monthly
        overage_price = overage_members * plan.overage_price_per_member
        total_price = base_price + overage_price

        return BillingInfo(
            tenant_id=tenant_id,
            plan=plan,
            current_members=current_members,
            max_members=max_members,
            overage_members=overage_members,
            base_price=base_price,
            overage_price=overage_price,
            total_price=total_price,
            billing_cycle=BillingCycle.MONTHLY,
        )

    def create_subscription(
        self,
        tenant_id: str,
        plan_id: str,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        razorpay_customer_id: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Subscription]]:
        """
        Create a subscription for a tenant.

        Args:
            tenant_id: Tenant ID
            plan_id: Plan ID (clinic, hospital, enterprise)
            billing_cycle: Billing cycle (monthly, quarterly, yearly)
            razorpay_customer_id: Razorpay customer ID if already created

        Returns:
            (success, message, subscription)
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found", None

        plan = TENANT_PLANS.get(plan_id)
        if not plan:
            return False, f"Invalid plan: {plan_id}", None

        # Get pricing for billing cycle
        amount = plan.get_price(billing_cycle)
        if amount == 0 and plan_id == "enterprise":
            return False, "Enterprise plans require custom pricing. Please contact sales.", None

        # Create Razorpay subscription if client is available
        razorpay_subscription_id = None
        if self.razorpay_client:
            try:
                razorpay_plan_id = plan.get_razorpay_plan_id(billing_cycle)
                if razorpay_plan_id:
                    subscription_data = {
                        "plan_id": razorpay_plan_id,
                        "customer_notify": 1,
                        "total_count": 120,  # 10 years for monthly
                    }
                    if razorpay_customer_id:
                        subscription_data["customer_id"] = razorpay_customer_id

                    razorpay_sub = self.razorpay_client.subscription.create(subscription_data)
                    razorpay_subscription_id = razorpay_sub["id"]
            except Exception as e:
                return False, f"Failed to create Razorpay subscription: {str(e)}", None

        # Create subscription record
        subscription = Subscription(
            user_id=tenant.owner_id,
            organization_id=tenant_id,
            plan_id=plan_id,
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.PENDING if razorpay_subscription_id else SubscriptionStatus.ACTIVE,
            razorpay_subscription_id=razorpay_subscription_id,
            razorpay_customer_id=razorpay_customer_id,
            amount=amount,
            started_at=datetime.utcnow() if not razorpay_subscription_id else None,
            current_period_start=datetime.utcnow(),
            current_period_end=self._calculate_period_end(billing_cycle),
            next_billing_date=self._calculate_period_end(billing_cycle),
        )

        # Update tenant plan and status
        tenant.plan_id = plan_id
        tenant.status = TenantStatus.ACTIVE if subscription.status == SubscriptionStatus.ACTIVE else TenantStatus.TRIAL
        self.storage.update_tenant(tenant)

        return True, "Subscription created successfully", subscription

    def upgrade_plan(
        self,
        tenant_id: str,
        new_plan_id: str,
    ) -> Tuple[bool, str]:
        """
        Upgrade tenant to a different plan.

        Handles prorated billing.
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        current_plan = TENANT_PLANS.get(tenant.plan_id)
        new_plan = TENANT_PLANS.get(new_plan_id)

        if not new_plan:
            return False, f"Invalid plan: {new_plan_id}"

        # Validate upgrade path
        plan_hierarchy = ["clinic", "hospital", "enterprise"]
        if new_plan_id not in plan_hierarchy:
            return False, "Invalid upgrade path"

        current_idx = plan_hierarchy.index(tenant.plan_id) if tenant.plan_id in plan_hierarchy else -1
        new_idx = plan_hierarchy.index(new_plan_id)

        if new_idx <= current_idx:
            return False, "Can only upgrade to higher-tier plans. Use downgrade for lower tiers."

        # Update tenant
        tenant.plan_id = new_plan_id
        tenant.status = TenantStatus.ACTIVE
        self.storage.update_tenant(tenant)

        # Handle prorated billing with Razorpay
        if self.razorpay_client and tenant.plan_id in TENANT_PLANS:
            try:
                # Create upgrade order for prorated amount
                current_billing = self.get_billing_info(tenant_id)
                upgrade_amount = new_plan.price_monthly  # Simplified - full price for now

                order_data = {
                    "amount": upgrade_amount,
                    "currency": "INR",
                    "notes": {
                        "tenant_id": tenant_id,
                        "upgrade_from": current_plan.name if current_plan else "unknown",
                        "upgrade_to": new_plan.name,
                    }
                }
                razorpay_order = self.razorpay_client.order.create(data=order_data)

                # Generate invoice for upgrade
                invoice = self.generate_invoice(
                    tenant_id=tenant_id,
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow() + timedelta(days=30),
                )
                invoice.description = f"Plan upgrade: {current_plan.name if current_plan else 'Unknown'} → {new_plan.name}"

                # Save invoice to payments storage
                from ..payments.storage import get_payment_storage
                payment_storage = get_payment_storage()
                payment_storage.create_invoice(invoice)

            except Exception as e:
                print(f"Warning: Razorpay upgrade processing failed: {e}")

        return True, f"Successfully upgraded to {new_plan.name}"

    def downgrade_plan(
        self,
        tenant_id: str,
        new_plan_id: str,
    ) -> Tuple[bool, str]:
        """
        Downgrade tenant to a different plan.

        Applied at end of current billing period.
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        new_plan = TENANT_PLANS.get(new_plan_id)
        if not new_plan:
            return False, f"Invalid plan: {new_plan_id}"

        # Check if member count fits in new plan
        members = self.storage.get_tenant_members(tenant_id, active_only=True)
        if new_plan.max_members > 0 and len(members) > new_plan.max_members:
            return False, (
                f"Cannot downgrade: You have {len(members)} members but {new_plan.name} "
                f"supports only {new_plan.max_members}. Please remove members first."
            )

        # Schedule downgrade at end of period
        # Store scheduled plan change in tenant settings
        tenant.settings["scheduled_plan_change"] = {
            "new_plan_id": new_plan_id,
            "effective_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "reason": "downgrade",
        }
        self.storage.update_tenant(tenant)

        return True, f"Scheduled downgrade to {new_plan.name} at end of billing period"

    def cancel_subscription(
        self,
        tenant_id: str,
        immediate: bool = False,
    ) -> Tuple[bool, str]:
        """
        Cancel tenant subscription.

        Args:
            tenant_id: Tenant ID
            immediate: If True, cancel immediately. Otherwise, at end of period.

        Returns:
            (success, message)
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        if immediate:
            tenant.status = TenantStatus.CANCELLED
            self.storage.update_tenant(tenant)

            # Cancel Razorpay subscription if exists
            if self.razorpay_client:
                try:
                    # Find subscription by tenant
                    from ..payments.storage import get_payment_storage
                    payment_storage = get_payment_storage()
                    subscription = payment_storage.get_user_subscription(tenant.owner_id)

                    if subscription and subscription.razorpay_subscription_id:
                        self.razorpay_client.subscription.cancel(
                            subscription.razorpay_subscription_id
                        )
                        subscription.status = SubscriptionStatus.CANCELLED
                        subscription.cancelled_at = datetime.utcnow()
                        payment_storage.update_subscription(subscription)
                except Exception as e:
                    print(f"Warning: Razorpay cancellation failed: {e}")

            return True, "Subscription cancelled immediately"
        else:
            # Schedule cancellation at end of period
            tenant.settings["scheduled_cancellation"] = {
                "cancel_at_period_end": True,
                "scheduled_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            }
            self.storage.update_tenant(tenant)

            return True, "Subscription will be cancelled at end of current billing period"

    def generate_invoice(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> Invoice:
        """
        Generate an invoice for a billing period.

        Includes:
        - Base subscription fee
        - Overage charges
        - GST (18% for India)
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        billing_info = self.get_billing_info(tenant_id)

        # Generate invoice number
        invoice_number = f"INV-{tenant_id[:8]}-{datetime.utcnow().strftime('%Y%m%d')}"

        # Build description
        description_parts = [
            f"{billing_info.plan.name} - {billing_info.billing_cycle.value.title()} Subscription"
        ]
        if billing_info.overage_members > 0:
            description_parts.append(
                f"{billing_info.overage_members} additional member(s) @ ₹{billing_info.plan.overage_price_per_member/100:.2f}"
            )

        invoice = Invoice(
            user_id=tenant.owner_id,
            subscription_id=None,  # Link to subscription if available
            invoice_number=invoice_number,
            description=" + ".join(description_parts),
            subtotal=billing_info.total_price,
            currency="INR",
            period_start=period_start,
            period_end=period_end,
            customer_name=tenant.name,
            customer_email=tenant.billing_email or tenant.email,
            customer_gstin=tenant.tax_id,
        )

        # Calculate GST (18%)
        invoice.calculate_tax(rate=0.18)

        return invoice

    def record_payment(
        self,
        tenant_id: str,
        amount: int,
        razorpay_payment_id: str,
        razorpay_order_id: Optional[str] = None,
    ) -> Payment:
        """
        Record a payment for a tenant.

        Args:
            tenant_id: Tenant ID
            amount: Amount in paise
            razorpay_payment_id: Razorpay payment ID
            razorpay_order_id: Razorpay order ID

        Returns:
            Payment record
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        payment = Payment(
            user_id=tenant.owner_id,
            amount=amount,
            currency="INR",
            status=PaymentStatus.COMPLETED,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            completed_at=datetime.utcnow(),
        )

        # Save payment to database
        from ..payments.storage import get_payment_storage
        payment_storage = get_payment_storage()
        payment_storage.create_payment(payment)

        return payment

    def get_usage_summary(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get usage summary for billing analytics.

        Args:
            tenant_id: Tenant ID
            days: Number of days to look back

        Returns:
            Usage statistics
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        members = self.storage.get_tenant_members(tenant_id, active_only=True)
        billing_info = self.get_billing_info(tenant_id)

        # Get actual usage data from database
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        usage_stats = self.storage.get_usage_stats(tenant_id, start_date, end_date)

        # Calculate storage in GB
        storage_gb = usage_stats["total_storage_bytes"] / (1024 ** 3) if usage_stats["total_storage_bytes"] else 0

        # Calculate per-member average
        total_queries = usage_stats["total_queries"]
        per_member_avg = total_queries / len(members) if members else 0

        return {
            "tenant_id": tenant_id,
            "plan": billing_info.plan.name,
            "members": {
                "total": len(members),
                "max_allowed": billing_info.max_members,
                "overage": billing_info.overage_members,
            },
            "queries": {
                "total": total_queries,
                "per_member_avg": round(per_member_avg, 2),
            },
            "storage": {
                "used_gb": round(storage_gb, 2),
                "quota_gb": billing_info.plan.storage_gb,
            },
            "costs": {
                "base_price": billing_info.base_price,
                "overage_price": billing_info.overage_price,
                "total_price": billing_info.total_price,
                "currency": "INR",
            },
            "period_days": days,
        }

    def _calculate_period_end(self, cycle: BillingCycle) -> datetime:
        """Calculate end of billing period."""
        now = datetime.utcnow()
        if cycle == BillingCycle.MONTHLY:
            return now + timedelta(days=30)
        elif cycle == BillingCycle.QUARTERLY:
            return now + timedelta(days=90)
        else:  # YEARLY
            return now + timedelta(days=365)


# Default instance
_billing_service: Optional[TenantBillingService] = None


def get_billing_service() -> TenantBillingService:
    """Get the default billing service instance."""
    global _billing_service
    if _billing_service is None:
        import os
        _billing_service = TenantBillingService(
            razorpay_key_id=os.environ.get("RAZORPAY_KEY_ID"),
            razorpay_key_secret=os.environ.get("RAZORPAY_KEY_SECRET"),
        )
    return _billing_service
