"""
Consultation Payments

Handle consultation payments with Razorpay, escrow, and specialist payouts.
Revenue sharing: Platform takes 15%, specialist gets 85%.
"""

from datetime import datetime, timedelta
from typing import Optional

from src.peers.models import (
    ConsultPayment,
    SpecialistPayout,
    PaymentStatus,
)


class ConsultationPaymentManager:
    """Manages consultation payments and payouts."""

    # Platform revenue share (15%)
    PLATFORM_FEE_PERCENTAGE = 0.15

    def __init__(self):
        """Initialize payment manager."""
        # In production, integrate with Razorpay
        self.payments: dict[str, ConsultPayment] = {}
        self.payouts: dict[str, SpecialistPayout] = {}

    def create_payment(
        self,
        consult_request_id: str,
        payer_id: str,
        payee_id: str,
        amount: int,
    ) -> ConsultPayment:
        """
        Create a consultation payment.

        Args:
            consult_request_id: Consultation request ID
            payer_id: Requesting doctor ID
            payee_id: Specialist ID
            amount: Amount in paise

        Returns:
            ConsultPayment object
        """
        # Calculate platform fee and specialist payout
        platform_fee = int(amount * self.PLATFORM_FEE_PERCENTAGE)
        specialist_payout = amount - platform_fee

        payment = ConsultPayment(
            consult_request_id=consult_request_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount=amount,
            platform_fee=platform_fee,
            specialist_payout=specialist_payout,
        )

        self.payments[payment.id] = payment
        return payment

    def process_payment(
        self,
        payment_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
    ) -> Optional[ConsultPayment]:
        """
        Process payment after Razorpay confirmation.

        Args:
            payment_id: Payment ID
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID

        Returns:
            Updated payment or None
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return None

        payment.status = PaymentStatus.PAID
        payment.razorpay_order_id = razorpay_order_id
        payment.razorpay_payment_id = razorpay_payment_id
        payment.updated_at = datetime.utcnow()

        # Hold in escrow
        return self.hold_in_escrow(payment_id)

    def hold_in_escrow(
        self,
        payment_id: str,
    ) -> Optional[ConsultPayment]:
        """
        Hold payment in escrow until consultation complete.

        Args:
            payment_id: Payment ID

        Returns:
            Updated payment or None
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return None

        payment.status = PaymentStatus.IN_ESCROW
        payment.held_in_escrow_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()

        # Auto-release after 7 days
        payment.auto_release_at = datetime.utcnow() + timedelta(days=7)

        return payment

    def release_payment(
        self,
        payment_id: str,
    ) -> Optional[ConsultPayment]:
        """
        Release payment from escrow to specialist.

        Args:
            payment_id: Payment ID

        Returns:
            Updated payment or None
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return None

        if payment.status != PaymentStatus.IN_ESCROW:
            return None

        payment.status = PaymentStatus.RELEASED
        payment.released_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()

        return payment

    def refund_payment(
        self,
        payment_id: str,
        reason: str,
    ) -> Optional[ConsultPayment]:
        """
        Refund payment to requesting doctor.

        Args:
            payment_id: Payment ID
            reason: Refund reason

        Returns:
            Updated payment or None
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return None

        # In production, process Razorpay refund
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.utcnow()
        payment.refund_reason = reason
        payment.updated_at = datetime.utcnow()

        return payment

    def auto_release_due_payments(self) -> list[str]:
        """
        Auto-release payments past auto-release date.

        Returns:
            List of released payment IDs
        """
        released_ids = []
        now = datetime.utcnow()

        for payment in self.payments.values():
            if (
                payment.status == PaymentStatus.IN_ESCROW
                and payment.auto_release_at
                and payment.auto_release_at <= now
            ):
                self.release_payment(payment.id)
                released_ids.append(payment.id)

        return released_ids

    def get_payment(self, payment_id: str) -> Optional[ConsultPayment]:
        """
        Get payment by ID.

        Args:
            payment_id: Payment ID

        Returns:
            ConsultPayment or None
        """
        return self.payments.get(payment_id)

    def get_payment_for_consultation(
        self,
        consult_request_id: str,
    ) -> Optional[ConsultPayment]:
        """
        Get payment for consultation request.

        Args:
            consult_request_id: Consultation request ID

        Returns:
            ConsultPayment or None
        """
        for payment in self.payments.values():
            if payment.consult_request_id == consult_request_id:
                return payment
        return None

    def get_specialist_earnings(
        self,
        specialist_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> dict[str, int]:
        """
        Get specialist earnings for period.

        Args:
            specialist_id: Specialist ID
            period_start: Start date
            period_end: End date

        Returns:
            Earnings summary
        """
        if period_start is None:
            period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period_end is None:
            period_end = datetime.utcnow()

        payments = [
            p for p in self.payments.values()
            if p.payee_id == specialist_id
            and p.created_at >= period_start
            and p.created_at <= period_end
        ]

        total_earnings = sum(p.specialist_payout for p in payments if p.status == PaymentStatus.RELEASED)
        pending_earnings = sum(p.specialist_payout for p in payments if p.status == PaymentStatus.IN_ESCROW)
        platform_fees = sum(p.platform_fee for p in payments if p.status in [PaymentStatus.RELEASED, PaymentStatus.IN_ESCROW])

        return {
            "total_earnings": total_earnings,
            "pending_earnings": pending_earnings,
            "platform_fees": platform_fees,
            "total_consultations": len(payments),
        }

    def create_payout(
        self,
        specialist_id: str,
        period_start: datetime,
        period_end: datetime,
        bank_account_number: Optional[str] = None,
        ifsc_code: Optional[str] = None,
        upi_id: Optional[str] = None,
    ) -> SpecialistPayout:
        """
        Create payout for specialist.

        Args:
            specialist_id: Specialist ID
            period_start: Period start date
            period_end: Period end date
            bank_account_number: Bank account
            ifsc_code: IFSC code
            upi_id: UPI ID

        Returns:
            SpecialistPayout object
        """
        # Get released payments
        payments = [
            p for p in self.payments.values()
            if p.payee_id == specialist_id
            and p.status == PaymentStatus.RELEASED
            and p.released_at
            and p.released_at >= period_start
            and p.released_at <= period_end
        ]

        total_earnings = sum(p.specialist_payout for p in payments)
        platform_fees = sum(p.platform_fee for p in payments)

        payout = SpecialistPayout(
            specialist_id=specialist_id,
            period_start=period_start,
            period_end=period_end,
            total_earnings=total_earnings,
            platform_fees=platform_fees,
            payout_amount=total_earnings,
            consult_payment_ids=[p.id for p in payments],
            total_consultations=len(payments),
            bank_account_number=bank_account_number,
            ifsc_code=ifsc_code,
            upi_id=upi_id,
        )

        self.payouts[payout.id] = payout
        return payout

    def process_payout(
        self,
        payout_id: str,
        transaction_id: str,
    ) -> Optional[SpecialistPayout]:
        """
        Mark payout as processed.

        Args:
            payout_id: Payout ID
            transaction_id: Bank transaction ID

        Returns:
            Updated payout or None
        """
        payout = self.payouts.get(payout_id)
        if not payout:
            return None

        payout.is_processed = True
        payout.processed_at = datetime.utcnow()
        payout.transaction_id = transaction_id

        return payout

    def get_pending_payouts(self) -> list[SpecialistPayout]:
        """
        Get pending payouts.

        Returns:
            List of pending payouts
        """
        pending = [p for p in self.payouts.values() if not p.is_processed]
        pending.sort(key=lambda p: p.created_at)
        return pending

    def get_specialist_payouts(
        self,
        specialist_id: str,
    ) -> list[SpecialistPayout]:
        """
        Get all payouts for specialist.

        Args:
            specialist_id: Specialist ID

        Returns:
            List of payouts
        """
        payouts = [
            p for p in self.payouts.values()
            if p.specialist_id == specialist_id
        ]
        payouts.sort(key=lambda p: p.created_at, reverse=True)
        return payouts

    def calculate_platform_revenue(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, int]:
        """
        Calculate platform revenue for period.

        Args:
            period_start: Start date
            period_end: End date

        Returns:
            Revenue summary
        """
        payments = [
            p for p in self.payments.values()
            if p.created_at >= period_start
            and p.created_at <= period_end
            and p.status in [PaymentStatus.RELEASED, PaymentStatus.IN_ESCROW]
        ]

        total_revenue = sum(p.platform_fee for p in payments)
        total_volume = sum(p.amount for p in payments)
        specialist_payouts = sum(p.specialist_payout for p in payments)

        return {
            "total_revenue": total_revenue,
            "total_volume": total_volume,
            "specialist_payouts": specialist_payouts,
            "total_transactions": len(payments),
        }

    def create_razorpay_order(
        self,
        payment_id: str,
    ) -> dict[str, str]:
        """
        Create Razorpay order for payment.

        Args:
            payment_id: Payment ID

        Returns:
            Razorpay order details
        """
        payment = self.payments.get(payment_id)
        if not payment:
            return {}

        # In production, integrate with Razorpay SDK
        # For now, return placeholder
        order_id = f"order_{payment_id[:8]}"

        payment.razorpay_order_id = order_id
        payment.updated_at = datetime.utcnow()

        return {
            "order_id": order_id,
            "amount": payment.amount,
            "currency": payment.currency,
        }

    def verify_razorpay_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verify Razorpay payment signature.

        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Payment signature

        Returns:
            True if valid
        """
        # In production, verify using Razorpay SDK
        # For now, return True
        return True
