"""
Payment Storage

SQLite-based storage for payment data.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Generator

from .models import (
    PaymentPlan, Subscription, Payment, Invoice,
    PaymentStatus, SubscriptionStatus, BillingCycle, PLANS
)


class PaymentStorage:
    """SQLite storage for payment data."""

    def __init__(self, db_path: str = "data/payments.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Subscriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    organization_id TEXT,

                    plan_id TEXT NOT NULL,
                    billing_cycle TEXT NOT NULL,

                    status TEXT NOT NULL DEFAULT 'pending',

                    razorpay_subscription_id TEXT,
                    razorpay_customer_id TEXT,

                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    current_period_start TEXT,
                    current_period_end TEXT,
                    cancelled_at TEXT,
                    ended_at TEXT,

                    next_billing_date TEXT,
                    amount INTEGER DEFAULT 0,

                    trial_ends_at TEXT,
                    is_trial INTEGER DEFAULT 0
                )
            """)

            # Payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    subscription_id TEXT,

                    amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'INR',

                    status TEXT NOT NULL DEFAULT 'pending',

                    razorpay_order_id TEXT,
                    razorpay_payment_id TEXT,
                    razorpay_signature TEXT,

                    method TEXT,

                    created_at TEXT NOT NULL,
                    completed_at TEXT,

                    error_code TEXT,
                    error_description TEXT,

                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                )
            """)

            # Invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    subscription_id TEXT,
                    payment_id TEXT,

                    invoice_number TEXT UNIQUE NOT NULL,
                    description TEXT,

                    subtotal INTEGER NOT NULL,
                    tax_amount INTEGER DEFAULT 0,
                    total INTEGER NOT NULL,
                    currency TEXT DEFAULT 'INR',

                    is_paid INTEGER DEFAULT 0,
                    paid_at TEXT,

                    period_start TEXT,
                    period_end TEXT,

                    created_at TEXT NOT NULL,
                    due_date TEXT,

                    customer_name TEXT,
                    customer_email TEXT,
                    customer_gstin TEXT,
                    billing_address TEXT,

                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
                    FOREIGN KEY (payment_id) REFERENCES payments(id)
                )
            """)

            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_user ON subscriptions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_status ON subscriptions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pay_user ON payments(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pay_status ON payments(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_user ON invoices(user_id)")

            conn.commit()

    # Subscription operations
    def create_subscription(self, sub: Subscription) -> Subscription:
        """Create a subscription."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO subscriptions (
                    id, user_id, organization_id, plan_id, billing_cycle, status,
                    razorpay_subscription_id, razorpay_customer_id,
                    created_at, started_at, current_period_start, current_period_end,
                    cancelled_at, ended_at, next_billing_date, amount,
                    trial_ends_at, is_trial
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub.id, sub.user_id, sub.organization_id, sub.plan_id,
                sub.billing_cycle.value, sub.status.value,
                sub.razorpay_subscription_id, sub.razorpay_customer_id,
                sub.created_at.isoformat(),
                sub.started_at.isoformat() if sub.started_at else None,
                sub.current_period_start.isoformat() if sub.current_period_start else None,
                sub.current_period_end.isoformat() if sub.current_period_end else None,
                sub.cancelled_at.isoformat() if sub.cancelled_at else None,
                sub.ended_at.isoformat() if sub.ended_at else None,
                sub.next_billing_date.isoformat() if sub.next_billing_date else None,
                sub.amount,
                sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
                sub.is_trial,
            ))
            conn.commit()
        return sub

    def get_subscription(self, sub_id: str) -> Optional[Subscription]:
        """Get subscription by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_subscription(row)
        return None

    def get_subscription_by_razorpay_id(self, razorpay_id: str) -> Optional[Subscription]:
        """Get subscription by Razorpay ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM subscriptions WHERE razorpay_subscription_id = ?",
                (razorpay_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_subscription(row)
        return None

    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get active subscription for user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions
                WHERE user_id = ? AND status IN ('active', 'pending')
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_subscription(row)
        return None

    def get_user_subscriptions(self, user_id: str) -> list[Subscription]:
        """Get all subscriptions for user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return [self._row_to_subscription(row) for row in cursor.fetchall()]

    def update_subscription(self, sub: Subscription) -> Subscription:
        """Update subscription."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE subscriptions SET
                    plan_id = ?, billing_cycle = ?, status = ?,
                    razorpay_subscription_id = ?, razorpay_customer_id = ?,
                    started_at = ?, current_period_start = ?, current_period_end = ?,
                    cancelled_at = ?, ended_at = ?, next_billing_date = ?, amount = ?,
                    trial_ends_at = ?, is_trial = ?
                WHERE id = ?
            """, (
                sub.plan_id, sub.billing_cycle.value, sub.status.value,
                sub.razorpay_subscription_id, sub.razorpay_customer_id,
                sub.started_at.isoformat() if sub.started_at else None,
                sub.current_period_start.isoformat() if sub.current_period_start else None,
                sub.current_period_end.isoformat() if sub.current_period_end else None,
                sub.cancelled_at.isoformat() if sub.cancelled_at else None,
                sub.ended_at.isoformat() if sub.ended_at else None,
                sub.next_billing_date.isoformat() if sub.next_billing_date else None,
                sub.amount,
                sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
                sub.is_trial,
                sub.id,
            ))
            conn.commit()
        return sub

    # Payment operations
    def create_payment(self, payment: Payment) -> Payment:
        """Create a payment record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments (
                    id, user_id, subscription_id, amount, currency, status,
                    razorpay_order_id, razorpay_payment_id, razorpay_signature,
                    method, created_at, completed_at, error_code, error_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment.id, payment.user_id, payment.subscription_id,
                payment.amount, payment.currency, payment.status.value,
                payment.razorpay_order_id, payment.razorpay_payment_id,
                payment.razorpay_signature, payment.method,
                payment.created_at.isoformat(),
                payment.completed_at.isoformat() if payment.completed_at else None,
                payment.error_code, payment.error_description,
            ))
            conn.commit()
        return payment

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_payment(row)
        return None

    def get_payment_by_razorpay_id(self, razorpay_id: str) -> Optional[Payment]:
        """Get payment by Razorpay payment ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE razorpay_payment_id = ?",
                (razorpay_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_payment(row)
        return None

    def get_user_payments(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        """Get payments for user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM payments
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [self._row_to_payment(row) for row in cursor.fetchall()]

    def update_payment(self, payment: Payment) -> Payment:
        """Update payment record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE payments SET
                    status = ?, razorpay_payment_id = ?, razorpay_signature = ?,
                    method = ?, completed_at = ?, error_code = ?, error_description = ?
                WHERE id = ?
            """, (
                payment.status.value, payment.razorpay_payment_id,
                payment.razorpay_signature, payment.method,
                payment.completed_at.isoformat() if payment.completed_at else None,
                payment.error_code, payment.error_description,
                payment.id,
            ))
            conn.commit()
        return payment

    # Invoice operations
    def create_invoice(self, invoice: Invoice) -> Invoice:
        """Create an invoice."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (
                    id, user_id, subscription_id, payment_id,
                    invoice_number, description,
                    subtotal, tax_amount, total, currency,
                    is_paid, paid_at, period_start, period_end,
                    created_at, due_date,
                    customer_name, customer_email, customer_gstin, billing_address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice.id, invoice.user_id, invoice.subscription_id,
                invoice.payment_id, invoice.invoice_number, invoice.description,
                invoice.subtotal, invoice.tax_amount, invoice.total, invoice.currency,
                invoice.is_paid,
                invoice.paid_at.isoformat() if invoice.paid_at else None,
                invoice.period_start.isoformat() if invoice.period_start else None,
                invoice.period_end.isoformat() if invoice.period_end else None,
                invoice.created_at.isoformat(),
                invoice.due_date.isoformat() if invoice.due_date else None,
                invoice.customer_name, invoice.customer_email,
                invoice.customer_gstin, invoice.billing_address,
            ))
            conn.commit()
        return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_invoice(row)
        return None

    def get_user_invoices(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Invoice]:
        """Get invoices for user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM invoices
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            return [self._row_to_invoice(row) for row in cursor.fetchall()]

    def generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            year = datetime.utcnow().strftime("%Y")
            cursor.execute(
                "SELECT COUNT(*) FROM invoices WHERE invoice_number LIKE ?",
                (f"INV-{year}%",)
            )
            count = cursor.fetchone()[0] + 1
            return f"INV-{year}-{count:06d}"

    # Helper methods
    def _row_to_subscription(self, row: sqlite3.Row) -> Subscription:
        """Convert row to Subscription."""
        return Subscription(
            id=row["id"],
            user_id=row["user_id"],
            organization_id=row["organization_id"],
            plan_id=row["plan_id"],
            billing_cycle=BillingCycle(row["billing_cycle"]),
            status=SubscriptionStatus(row["status"]),
            razorpay_subscription_id=row["razorpay_subscription_id"],
            razorpay_customer_id=row["razorpay_customer_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            current_period_start=datetime.fromisoformat(row["current_period_start"]) if row["current_period_start"] else None,
            current_period_end=datetime.fromisoformat(row["current_period_end"]) if row["current_period_end"] else None,
            cancelled_at=datetime.fromisoformat(row["cancelled_at"]) if row["cancelled_at"] else None,
            ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
            next_billing_date=datetime.fromisoformat(row["next_billing_date"]) if row["next_billing_date"] else None,
            amount=row["amount"],
            trial_ends_at=datetime.fromisoformat(row["trial_ends_at"]) if row["trial_ends_at"] else None,
            is_trial=bool(row["is_trial"]),
        )

    def _row_to_payment(self, row: sqlite3.Row) -> Payment:
        """Convert row to Payment."""
        return Payment(
            id=row["id"],
            user_id=row["user_id"],
            subscription_id=row["subscription_id"],
            amount=row["amount"],
            currency=row["currency"],
            status=PaymentStatus(row["status"]),
            razorpay_order_id=row["razorpay_order_id"],
            razorpay_payment_id=row["razorpay_payment_id"],
            razorpay_signature=row["razorpay_signature"],
            method=row["method"],
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            error_code=row["error_code"],
            error_description=row["error_description"],
        )

    def _row_to_invoice(self, row: sqlite3.Row) -> Invoice:
        """Convert row to Invoice."""
        return Invoice(
            id=row["id"],
            user_id=row["user_id"],
            subscription_id=row["subscription_id"],
            payment_id=row["payment_id"],
            invoice_number=row["invoice_number"],
            description=row["description"],
            subtotal=row["subtotal"],
            tax_amount=row["tax_amount"],
            total=row["total"],
            currency=row["currency"],
            is_paid=bool(row["is_paid"]),
            paid_at=datetime.fromisoformat(row["paid_at"]) if row["paid_at"] else None,
            period_start=datetime.fromisoformat(row["period_start"]) if row["period_start"] else None,
            period_end=datetime.fromisoformat(row["period_end"]) if row["period_end"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            customer_name=row["customer_name"],
            customer_email=row["customer_email"],
            customer_gstin=row["customer_gstin"],
            billing_address=row["billing_address"],
        )


# Default instance
_storage: Optional[PaymentStorage] = None


def get_payment_storage() -> PaymentStorage:
    """Get the default storage instance."""
    global _storage
    if _storage is None:
        _storage = PaymentStorage()
    return _storage
