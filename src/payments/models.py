"""
Payment Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"
    HALTED = "halted"


class BillingCycle(str, Enum):
    """Billing cycle."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PaymentPlan:
    """Subscription plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Pricing (in paise for INR)
    price_monthly: int = 0  # e.g., 99900 = ₹999
    price_quarterly: int = 0
    price_yearly: int = 0

    # Currency
    currency: str = "INR"

    # Features
    daily_queries: int = 10
    drug_interactions: bool = True
    voice_input: bool = False
    offline_mode: bool = False
    emr_integration: bool = False
    priority_support: bool = False
    academic_writing: bool = False

    # Limits
    max_team_members: int = 1
    storage_gb: int = 1

    # Razorpay plan IDs
    razorpay_plan_monthly: Optional[str] = None
    razorpay_plan_quarterly: Optional[str] = None
    razorpay_plan_yearly: Optional[str] = None

    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_price(self, cycle: BillingCycle) -> int:
        """Get price for billing cycle."""
        if cycle == BillingCycle.MONTHLY:
            return self.price_monthly
        elif cycle == BillingCycle.QUARTERLY:
            return self.price_quarterly
        else:
            return self.price_yearly

    def get_razorpay_plan_id(self, cycle: BillingCycle) -> Optional[str]:
        """Get Razorpay plan ID for billing cycle."""
        if cycle == BillingCycle.MONTHLY:
            return self.razorpay_plan_monthly
        elif cycle == BillingCycle.QUARTERLY:
            return self.razorpay_plan_quarterly
        else:
            return self.razorpay_plan_yearly

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price_monthly": self.price_monthly,
            "price_quarterly": self.price_quarterly,
            "price_yearly": self.price_yearly,
            "currency": self.currency,
            "features": {
                "daily_queries": self.daily_queries,
                "drug_interactions": self.drug_interactions,
                "voice_input": self.voice_input,
                "offline_mode": self.offline_mode,
                "emr_integration": self.emr_integration,
                "priority_support": self.priority_support,
                "academic_writing": self.academic_writing,
                "max_team_members": self.max_team_members,
                "storage_gb": self.storage_gb,
            },
            "is_active": self.is_active,
        }


# Pre-defined plans matching CLAUDE.md pricing
PLANS = {
    "free": PaymentPlan(
        id="free",
        name="Free",
        description="Basic access for evaluation",
        price_monthly=0,
        price_quarterly=0,
        price_yearly=0,
        daily_queries=10,
        drug_interactions=True,
        voice_input=False,
        offline_mode=False,
    ),
    "essential": PaymentPlan(
        id="essential",
        name="Essential",
        description="For individual practitioners",
        price_monthly=99900,  # ₹999
        price_quarterly=269700,  # ₹899 x 3
        price_yearly=959900,  # ₹799.91 x 12 (₹9,599)
        daily_queries=100,
        drug_interactions=True,
        voice_input=True,
        offline_mode=True,
        max_team_members=1,
        storage_gb=5,
    ),
    "professional": PaymentPlan(
        id="professional",
        name="Professional",
        description="For busy clinicians",
        price_monthly=199900,  # ₹1,999
        price_quarterly=539700,  # ₹1,799 x 3
        price_yearly=1919900,  # ₹1,599.91 x 12 (₹19,199)
        daily_queries=500,
        drug_interactions=True,
        voice_input=True,
        offline_mode=True,
        emr_integration=True,
        priority_support=True,
        max_team_members=3,
        storage_gb=20,
    ),
    "clinic": PaymentPlan(
        id="clinic",
        name="Clinic",
        description="For small clinics and group practices",
        price_monthly=499900,  # ₹4,999
        price_quarterly=1349700,  # ₹4,499 x 3
        price_yearly=4799900,  # ₹3,999.91 x 12 (₹47,999)
        daily_queries=2000,
        drug_interactions=True,
        voice_input=True,
        offline_mode=True,
        emr_integration=True,
        priority_support=True,
        academic_writing=True,
        max_team_members=10,
        storage_gb=100,
    ),
}


@dataclass
class Subscription:
    """User subscription."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    organization_id: Optional[str] = None

    # Plan
    plan_id: str = "free"
    billing_cycle: BillingCycle = BillingCycle.MONTHLY

    # Status
    status: SubscriptionStatus = SubscriptionStatus.PENDING

    # Razorpay
    razorpay_subscription_id: Optional[str] = None
    razorpay_customer_id: Optional[str] = None

    # Dates
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Billing
    next_billing_date: Optional[datetime] = None
    amount: int = 0  # In paise

    # Trial
    trial_ends_at: Optional[datetime] = None
    is_trial: bool = False

    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "plan_id": self.plan_id,
            "billing_cycle": self.billing_cycle.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "amount": self.amount,
            "is_trial": self.is_trial,
        }


@dataclass
class Payment:
    """Payment record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    subscription_id: Optional[str] = None

    # Amount
    amount: int = 0  # In paise
    currency: str = "INR"

    # Status
    status: PaymentStatus = PaymentStatus.PENDING

    # Razorpay
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

    # Method
    method: Optional[str] = None  # card, upi, netbanking, wallet

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Error
    error_code: Optional[str] = None
    error_description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "method": self.method,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class Invoice:
    """Invoice for billing."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    subscription_id: Optional[str] = None
    payment_id: Optional[str] = None

    # Invoice details
    invoice_number: str = ""
    description: str = ""

    # Amount
    subtotal: int = 0
    tax_amount: int = 0  # GST
    total: int = 0
    currency: str = "INR"

    # Status
    is_paid: bool = False
    paid_at: Optional[datetime] = None

    # Period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None

    # Customer info
    customer_name: str = ""
    customer_email: str = ""
    customer_gstin: Optional[str] = None  # For Indian businesses
    billing_address: Optional[str] = None

    def calculate_tax(self, rate: float = 0.18) -> None:
        """Calculate GST (18% standard rate in India)."""
        self.tax_amount = int(self.subtotal * rate)
        self.total = self.subtotal + self.tax_amount

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "description": self.description,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "total": self.total,
            "currency": self.currency,
            "is_paid": self.is_paid,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
        }
