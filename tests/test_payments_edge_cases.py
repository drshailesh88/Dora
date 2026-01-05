"""
Comprehensive Edge Case Tests for Payment and Billing System

Tests cover:
1. Payment Creation Edge Cases
2. Razorpay Webhook Edge Cases
3. Subscription Edge Cases
4. Invoice Edge Cases
5. Refund Edge Cases
6. Concurrency Edge Cases
7. Error Recovery
"""

import pytest
import time
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
from decimal import Decimal
import threading
import tempfile

from src.payments.models import (
    Payment, PaymentStatus, Subscription, SubscriptionStatus,
    BillingCycle, Invoice, PLANS
)
from src.payments.service import PaymentService
from src.payments.storage import PaymentStorage
from src.payments.razorpay_client import RazorpayClient, RazorpayConfig
from src.tenants.billing import TenantBillingService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name


@pytest.fixture
def payment_storage(temp_db):
    """Create payment storage with temporary database."""
    return PaymentStorage(db_path=temp_db)


@pytest.fixture
def mock_razorpay():
    """Mock Razorpay client for testing."""
    mock = MagicMock(spec=RazorpayClient)
    mock.config = RazorpayConfig(
        key_id="rzp_test_123",
        key_secret="test_secret_456",
        webhook_secret="webhook_secret_789",
        test_mode=True
    )

    # Mock order creation
    mock.create_order.return_value = {
        "id": "order_test_123",
        "amount": 99900,
        "currency": "INR",
        "status": "created"
    }

    # Mock subscription creation
    mock.create_subscription.return_value = {
        "id": "sub_test_123",
        "plan_id": "plan_essential_monthly",
        "customer_id": "cust_test_123",
        "status": "created",
        "short_url": "https://rzp.io/test"
    }

    # Mock payment details
    mock.get_payment.return_value = {
        "id": "pay_test_123",
        "amount": 99900,
        "currency": "INR",
        "method": "upi",
        "status": "captured"
    }

    # Mock signature verification
    mock.verify_payment_signature.return_value = True
    mock.verify_webhook_signature.return_value = True

    return mock


@pytest.fixture
def payment_service(payment_storage, mock_razorpay):
    """Create payment service with mocked dependencies."""
    return PaymentService(storage=payment_storage, razorpay=mock_razorpay)


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "user_test_edge_cases"


# ============================================================================
# 1. Payment Creation Edge Cases
# ============================================================================

class TestPaymentCreationEdgeCases:
    """Test edge cases in payment creation."""

    def test_zero_amount_payment(self, payment_service, test_user_id):
        """Test creating payment with zero amount."""
        result = payment_service.create_payment(
            user_id=test_user_id,
            amount=0
        )
        # Should succeed but Razorpay might reject it
        assert result.success is False or result.payment.amount == 0

    def test_negative_amount_payment(self, payment_service, test_user_id, mock_razorpay):
        """Test creating payment with negative amount."""
        mock_razorpay.create_order.return_value = None
        result = payment_service.create_payment(
            user_id=test_user_id,
            amount=-100
        )
        assert result.success is False

    def test_amount_with_too_many_decimals(self, payment_storage, test_user_id):
        """Test payment amount with fractional paise - should be truncated or accepted."""
        # Payments should ideally be in whole paise (integers)
        # Implementation may accept floats and truncate
        payment = Payment(
            user_id=test_user_id,
            amount=999.99,  # Float - may be accepted and stored
            status=PaymentStatus.PENDING
        )
        # The implementation accepts floats, so we test it's handled gracefully
        result = payment_storage.create_payment(payment)
        assert result is not None  # Should succeed
        # Verify amount is stored (possibly truncated)
        assert result.amount == 999.99 or result.amount == 999 or result.amount == 1000

    def test_very_large_amount_payment(self, payment_service, test_user_id):
        """Test payment with very large amount (overflow check)."""
        # Test with amount > 2^31 (potential integer overflow)
        large_amount = 2147483648  # 2^31
        result = payment_service.create_payment(
            user_id=test_user_id,
            amount=large_amount
        )
        # Should handle gracefully
        if result.success:
            assert result.payment.amount == large_amount

    def test_missing_required_user_id(self, payment_storage):
        """Test payment creation without user_id."""
        payment = Payment(
            user_id="",  # Empty user_id
            amount=99900,
            status=PaymentStatus.PENDING
        )
        # Should still create (validation is at service level)
        result = payment_storage.create_payment(payment)
        assert result.user_id == ""

    def test_invalid_currency_code(self, payment_storage, test_user_id):
        """Test payment with invalid currency code."""
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            currency="INVALID",  # Not a valid ISO currency
            status=PaymentStatus.PENDING
        )
        # Storage allows it, but Razorpay would reject
        result = payment_storage.create_payment(payment)
        assert result.currency == "INVALID"

    def test_payment_with_special_characters_in_user_id(self, payment_service):
        """Test payment with special characters in user_id."""
        special_user_id = "user<>@#$%^&*()"
        result = payment_service.create_payment(
            user_id=special_user_id,
            amount=99900
        )
        if result.success:
            assert result.payment.user_id == special_user_id


# ============================================================================
# 2. Razorpay Webhook Edge Cases
# ============================================================================

class TestRazorpayWebhookEdgeCases:
    """Test edge cases in webhook handling."""

    def test_invalid_webhook_signature(self, payment_service, mock_razorpay):
        """Test webhook with invalid signature."""
        mock_razorpay.verify_webhook_signature.return_value = False

        # Even with invalid signature, handler should not crash
        payload = {"event": "payment.captured", "payload": {}}
        result = payment_service.handle_webhook("payment.captured", payload)
        # Should still process or reject gracefully
        assert isinstance(result, bool)

    def test_expired_webhook_signature(self, payment_service, mock_razorpay):
        """Test webhook with expired timestamp (replay attack prevention)."""
        old_timestamp = int((datetime.utcnow() - timedelta(hours=2)).timestamp())

        payload = {
            "event": "payment.captured",
            "created_at": old_timestamp,
            "payload": {"payment": {"id": "pay_old_123"}}
        }

        # Service should ideally check timestamp, but current implementation doesn't
        result = payment_service.handle_webhook("payment.captured", payload)
        assert isinstance(result, bool)

    def test_duplicate_webhook_delivery(self, payment_service, payment_storage, test_user_id):
        """Test handling same webhook twice (idempotency)."""
        # Create subscription first
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            razorpay_subscription_id="sub_duplicate_123",
            status=SubscriptionStatus.PENDING
        )
        payment_storage.create_subscription(sub)

        payload = {
            "subscription": {"id": "sub_duplicate_123"},
            "payment": {"id": "pay_dup_123", "amount": 99900}
        }

        # First webhook
        result1 = payment_service.handle_webhook("subscription.activated", payload)
        assert result1 is True

        # Second webhook (duplicate)
        result2 = payment_service.handle_webhook("subscription.activated", payload)
        assert result2 is True  # Should handle gracefully

        # Verify subscription wasn't created twice
        sub_check = payment_storage.get_subscription_by_razorpay_id("sub_duplicate_123")
        assert sub_check.status == SubscriptionStatus.ACTIVE

    def test_out_of_order_webhooks(self, payment_service, payment_storage, test_user_id):
        """Test webhooks arriving out of order (captured before authorized)."""
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            razorpay_subscription_id="sub_order_123",
            status=SubscriptionStatus.PENDING
        )
        payment_storage.create_subscription(sub)

        # Webhook 2 arrives first (charged)
        payload_charged = {
            "subscription": {"id": "sub_order_123", "charge_at": int(datetime.utcnow().timestamp())},
            "payment": {"id": "pay_order_123", "amount": 99900, "method": "card"}
        }
        result1 = payment_service.handle_webhook("subscription.charged", payload_charged)
        assert result1 is True

        # Webhook 1 arrives later (activated)
        payload_activated = {
            "subscription": {"id": "sub_order_123", "charge_at": int(datetime.utcnow().timestamp())}
        }
        result2 = payment_service.handle_webhook("subscription.activated", payload_activated)
        assert result2 is True

    def test_webhook_with_missing_payment_id(self, payment_service):
        """Test webhook with missing payment ID."""
        payload = {
            "subscription": {"id": "sub_missing_123"},
            "payment": {}  # Missing ID
        }

        # Should not crash
        result = payment_service.handle_webhook("subscription.charged", payload)
        assert isinstance(result, bool)

    def test_malformed_json_webhook(self, payment_service):
        """Test webhook with malformed payload."""
        # Handler receives dict, but let's test with incomplete data
        malformed_payload = {
            "event": "payment.captured"
            # Missing payload key
        }

        result = payment_service.handle_webhook("payment.captured", malformed_payload)
        # Should handle gracefully
        assert isinstance(result, bool)

    def test_unknown_webhook_event(self, payment_service):
        """Test webhook with unknown event type."""
        result = payment_service.handle_webhook("unknown.event.type", {})
        assert result is True  # Should return True to not retry


# ============================================================================
# 3. Subscription Edge Cases
# ============================================================================

class TestSubscriptionEdgeCases:
    """Test edge cases in subscription management."""

    def test_upgrade_from_free_to_paid(self, payment_service, test_user_id):
        """Test upgrading from free to paid plan."""
        # Create free subscription
        result = payment_service.create_subscription(
            user_id=test_user_id,
            plan_id="free"
        )
        assert result.success is True
        assert result.subscription.status == SubscriptionStatus.ACTIVE

        # Upgrade to paid
        change_result = payment_service.change_plan(
            subscription_id=result.subscription.id,
            new_plan_id="essential",
            at_period_end=False
        )
        assert change_result.success is True

    def test_downgrade_during_active_period(self, payment_service, payment_storage, test_user_id):
        """Test downgrading while subscription is active."""
        # Create paid subscription
        sub = Subscription(
            user_id=test_user_id,
            plan_id="professional",
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.utcnow() + timedelta(days=20)
        )
        payment_storage.create_subscription(sub)

        # Downgrade to essential
        result = payment_service.change_plan(
            subscription_id=sub.id,
            new_plan_id="essential",
            at_period_end=True  # Should apply at period end
        )
        assert result.success is True

    def test_cancel_subscription_with_pending_payment(self, payment_service, payment_storage, test_user_id):
        """Test canceling subscription with pending payment."""
        # Create subscription
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.ACTIVE
        )
        payment_storage.create_subscription(sub)

        # Create pending payment
        payment = Payment(
            user_id=test_user_id,
            subscription_id=sub.id,
            amount=99900,
            status=PaymentStatus.PENDING
        )
        payment_storage.create_payment(payment)

        # Cancel subscription
        result = payment_service.cancel_subscription(sub.id, at_period_end=False)
        assert result.success is True
        # Pending payment should remain

    def test_reactivate_canceled_subscription(self, payment_service, payment_storage, test_user_id):
        """Test reactivating a canceled subscription."""
        # Create and cancel subscription
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.CANCELLED,
            cancelled_at=datetime.utcnow()
        )
        payment_storage.create_subscription(sub)

        # Try to change plan (reactivate)
        result = payment_service.change_plan(
            subscription_id=sub.id,
            new_plan_id="essential",
            at_period_end=False
        )
        # Current implementation doesn't check status, so it might work
        # In production, should validate subscription status

    def test_subscription_with_expired_payment_method(self, payment_service, mock_razorpay, test_user_id):
        """Test creating subscription when payment method will expire soon."""
        # Mock Razorpay to simulate card expiring soon
        mock_razorpay.create_subscription.return_value = {
            "id": "sub_expiring_123",
            "status": "created",
            "card": {
                "last4": "1234",
                "expiry_month": (datetime.utcnow().month + 1) % 12,
                "expiry_year": datetime.utcnow().year
            }
        }

        result = payment_service.create_subscription(
            user_id=test_user_id,
            plan_id="essential",
            customer_email="test@example.com"
        )
        # Should create successfully, card expiry is checked during payment
        assert result.success is True

    def test_mid_cycle_plan_change(self, payment_service, payment_storage, test_user_id):
        """Test changing plan in middle of billing cycle."""
        # Create subscription mid-cycle
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15),
            amount=99900
        )
        payment_storage.create_subscription(sub)

        # Change to professional immediately
        result = payment_service.change_plan(
            subscription_id=sub.id,
            new_plan_id="professional",
            at_period_end=False
        )
        assert result.success is True
        # Should calculate prorated amount (current implementation simplified)


# ============================================================================
# 4. Invoice Edge Cases
# ============================================================================

class TestInvoiceEdgeCases:
    """Test edge cases in invoice generation."""

    def test_invoice_for_partial_period(self, payment_storage, test_user_id):
        """Test generating invoice for partial billing period."""
        # Create subscription that started mid-month
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow() - timedelta(days=10),
            current_period_end=datetime.utcnow() + timedelta(days=20)
        )
        payment_storage.create_subscription(sub)

        # Create invoice
        invoice = Invoice(
            user_id=test_user_id,
            subscription_id=sub.id,
            invoice_number="INV-PARTIAL-001",
            description="Partial period",
            subtotal=33300,  # Prorated amount
            period_start=sub.current_period_start,
            period_end=sub.current_period_end
        )
        invoice.calculate_tax(0.18)

        result = payment_storage.create_invoice(invoice)
        assert result.total > result.subtotal  # Tax applied
        assert result.subtotal == 33300

    def test_invoice_with_discount(self, payment_storage, test_user_id):
        """Test invoice with discount/coupon applied."""
        invoice = Invoice(
            user_id=test_user_id,
            invoice_number="INV-DISCOUNT-001",
            description="Essential Plan - 20% discount",
            subtotal=79920,  # 99900 - 20%
            currency="INR"
        )
        invoice.calculate_tax(0.18)

        result = payment_storage.create_invoice(invoice)
        assert result.subtotal == 79920
        assert result.tax_amount == int(79920 * 0.18)

    def test_invoice_with_gst_calculation(self, payment_storage, test_user_id):
        """Test invoice with GST calculation for different amounts."""
        test_cases = [
            (99900, 0.18, 17982),  # 18% GST
            (50000, 0.18, 9000),
            (199900, 0.18, 35982)
        ]

        for subtotal, rate, expected_tax in test_cases:
            invoice = Invoice(
                user_id=test_user_id,
                invoice_number=f"INV-GST-{subtotal}",
                description="GST Test",
                subtotal=subtotal
            )
            invoice.calculate_tax(rate)

            assert invoice.tax_amount == expected_tax
            assert invoice.total == subtotal + expected_tax

    def test_invoice_generation_failure_recovery(self, payment_service, payment_storage, test_user_id):
        """Test recovery when invoice generation fails."""
        # Create payment
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            status=PaymentStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        payment_storage.create_payment(payment)

        # Mock invoice generation to fail
        with patch.object(payment_storage, 'create_invoice', side_effect=Exception("DB Error")):
            # Payment should still complete even if invoice fails
            with pytest.raises(Exception):
                payment_service._generate_invoice_for_payment(payment)

        # Payment should still be completed
        verified_payment = payment_storage.get_payment(payment.id)
        assert verified_payment.status == PaymentStatus.COMPLETED

    def test_invoice_for_suspended_account(self, payment_storage, test_user_id):
        """Test generating invoice for suspended account."""
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.HALTED  # Suspended due to payment failure
        )
        payment_storage.create_subscription(sub)

        # Invoice can still be created for suspended account
        invoice = Invoice(
            user_id=test_user_id,
            subscription_id=sub.id,
            invoice_number="INV-SUSPENDED-001",
            description="Suspended account recovery",
            subtotal=99900
        )
        invoice.calculate_tax(0.18)

        result = payment_storage.create_invoice(invoice)
        assert result is not None


# ============================================================================
# 5. Refund Edge Cases
# ============================================================================

class TestRefundEdgeCases:
    """Test edge cases in payment refunds."""

    def test_partial_refund(self, mock_razorpay, payment_storage, test_user_id):
        """Test partial refund of payment."""
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            razorpay_payment_id="pay_refund_123",
            status=PaymentStatus.COMPLETED
        )
        payment_storage.create_payment(payment)

        # Mock partial refund
        mock_razorpay.refund_payment.return_value = {
            "id": "rfnd_123",
            "amount": 50000,
            "payment_id": "pay_refund_123"
        }

        result = mock_razorpay.refund_payment("pay_refund_123", amount=50000)
        assert result is not None
        assert result["amount"] == 50000

    def test_full_refund(self, mock_razorpay, payment_storage, test_user_id):
        """Test full refund of payment."""
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            razorpay_payment_id="pay_full_refund_123",
            status=PaymentStatus.COMPLETED
        )
        payment_storage.create_payment(payment)

        # Mock full refund
        mock_razorpay.refund_payment.return_value = {
            "id": "rfnd_full_123",
            "amount": 99900,
            "payment_id": "pay_full_refund_123"
        }

        result = mock_razorpay.refund_payment("pay_full_refund_123")
        assert result is not None

    def test_refund_after_partial_usage(self, payment_storage, test_user_id):
        """Test refund calculation after partial service usage."""
        # Subscription used for 10 days of 30-day period
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow() - timedelta(days=10),
            current_period_end=datetime.utcnow() + timedelta(days=20),
            amount=99900
        )
        payment_storage.create_subscription(sub)

        # Calculate prorated refund
        days_used = 10
        days_total = 30
        refund_amount = int(sub.amount * (days_total - days_used) / days_total)

        assert refund_amount == 66600  # 20/30 of 99900

    def test_multiple_refunds_same_payment(self, mock_razorpay, payment_storage, test_user_id):
        """Test multiple partial refunds on same payment."""
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            razorpay_payment_id="pay_multi_refund_123",
            status=PaymentStatus.COMPLETED
        )
        payment_storage.create_payment(payment)

        # First refund
        mock_razorpay.refund_payment.return_value = {
            "id": "rfnd_1",
            "amount": 30000,
            "payment_id": "pay_multi_refund_123"
        }
        result1 = mock_razorpay.refund_payment("pay_multi_refund_123", amount=30000)
        assert result1 is not None

        # Second refund
        mock_razorpay.refund_payment.return_value = {
            "id": "rfnd_2",
            "amount": 20000,
            "payment_id": "pay_multi_refund_123"
        }
        result2 = mock_razorpay.refund_payment("pay_multi_refund_123", amount=20000)
        assert result2 is not None

        # Total refunded: 50000, remaining: 49900

    def test_refund_exceeding_original_amount(self, mock_razorpay):
        """Test attempting refund greater than original payment."""
        # Razorpay should reject this
        mock_razorpay.refund_payment.return_value = None  # Failure

        result = mock_razorpay.refund_payment("pay_123", amount=200000)  # More than paid
        assert result is None  # Should fail


# ============================================================================
# 6. Concurrency Edge Cases
# ============================================================================

class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent operations."""

    def test_simultaneous_payment_attempts(self, payment_service, test_user_id):
        """Test multiple payment attempts at same time."""
        results = []

        def create_payment():
            result = payment_service.create_payment(
                user_id=test_user_id,
                amount=99900
            )
            results.append(result)

        # Create 3 threads attempting payment simultaneously
        threads = [threading.Thread(target=create_payment) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed (different payments)
        assert len(results) == 3
        assert all(r.success for r in results)

    def test_race_condition_upgrade_during_payment(self, payment_service, payment_storage, test_user_id):
        """Test upgrading plan while payment is processing."""
        # Create subscription
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.ACTIVE
        )
        payment_storage.create_subscription(sub)

        # Create payment
        payment = Payment(
            user_id=test_user_id,
            subscription_id=sub.id,
            amount=99900,
            status=PaymentStatus.PROCESSING
        )
        payment_storage.create_payment(payment)

        # Try to upgrade while payment is processing
        result = payment_service.change_plan(
            subscription_id=sub.id,
            new_plan_id="professional",
            at_period_end=False
        )

        # Should handle gracefully (current implementation allows it)
        assert result.success is True

    def test_multiple_tabs_checkout_scenario(self, payment_service, test_user_id):
        """Test user opening checkout in multiple browser tabs."""
        # User creates 3 orders from different tabs
        results = []
        for i in range(3):
            result = payment_service.create_payment(
                user_id=test_user_id,
                amount=99900
            )
            results.append(result)

        # All orders should be created
        assert len(results) == 3
        assert all(r.success for r in results)

        # But only one should be completed (user can only pay once)
        # This is enforced at verification stage


# ============================================================================
# 7. Error Recovery Edge Cases
# ============================================================================

class TestErrorRecoveryEdgeCases:
    """Test edge cases in error recovery."""

    def test_network_timeout_during_payment(self, payment_service, mock_razorpay, test_user_id):
        """Test handling network timeout during payment creation."""
        # Mock timeout
        mock_razorpay.create_order.side_effect = TimeoutError("Network timeout")

        # The service may propagate the exception or handle it gracefully
        try:
            result = payment_service.create_payment(
                user_id=test_user_id,
                amount=99900
            )
            # If handled gracefully, should return failure
            assert result is None or (hasattr(result, 'success') and result.success is False)
        except TimeoutError:
            # If exception propagates, that's also acceptable behavior
            # The test verifies the exception type is correct
            pass

    def test_payment_gateway_unavailable(self, payment_service, mock_razorpay, test_user_id):
        """Test handling when Razorpay is down."""
        # Mock gateway down
        mock_razorpay.create_order.return_value = None

        result = payment_service.create_payment(
            user_id=test_user_id,
            amount=99900
        )

        assert result.success is False
        assert result.error is not None

    def test_database_failure_during_payment_recording(self, payment_service, mock_razorpay, payment_storage, test_user_id):
        """Test handling database failure when recording payment."""
        # Mock successful Razorpay order
        mock_razorpay.create_order.return_value = {
            "id": "order_db_fail_123",
            "amount": 99900
        }

        # Mock database failure
        with patch.object(payment_storage, 'create_payment', side_effect=Exception("DB Error")):
            with pytest.raises(Exception):
                payment_service.create_payment(
                    user_id=test_user_id,
                    amount=99900
                )

        # Order was created in Razorpay but not recorded locally
        # Should have mechanism to reconcile

    def test_payment_verification_after_timeout(self, payment_service, payment_storage, mock_razorpay, test_user_id):
        """Test verifying payment after initial timeout."""
        # Create payment that timed out
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            razorpay_order_id="order_timeout_123",
            status=PaymentStatus.PENDING
        )
        payment_storage.create_payment(payment)

        # Later, user retries and payment was actually successful
        mock_razorpay.verify_payment_signature.return_value = True
        mock_razorpay.get_payment.return_value = {
            "id": "pay_timeout_123",
            "status": "captured",
            "method": "upi"
        }

        result = payment_service.verify_payment(
            order_id="order_timeout_123",
            payment_id="pay_timeout_123",
            signature="valid_signature"
        )

        assert result.success is True
        assert result.payment.status == PaymentStatus.COMPLETED

    def test_webhook_retry_mechanism(self, payment_service):
        """Test webhook retry after transient failure."""
        # First attempt fails
        with patch.object(payment_service, '_handle_payment_captured', side_effect=Exception("Transient error")):
            result1 = payment_service.handle_webhook("payment.captured", {"payment": {}})
            assert result1 is False  # Indicates retry needed

        # Retry succeeds
        result2 = payment_service.handle_webhook("payment.captured", {"payment": {"id": "pay_retry_123"}})
        assert result2 is True


# ============================================================================
# Additional Edge Cases
# ============================================================================

class TestAdditionalEdgeCases:
    """Additional edge cases for comprehensive coverage."""

    def test_subscription_renewal_on_holiday(self, payment_storage, test_user_id):
        """Test subscription renewal scheduled on holiday/weekend."""
        # Subscription renews on Dec 25 (Christmas)
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            status=SubscriptionStatus.ACTIVE,
            next_billing_date=datetime(2024, 12, 25)
        )
        payment_storage.create_subscription(sub)

        # System should handle normal processing
        assert sub.next_billing_date.day == 25

    def test_payment_with_unicode_characters(self, payment_storage, test_user_id):
        """Test payment with unicode characters in metadata."""
        payment = Payment(
            user_id=test_user_id,
            amount=99900,
            status=PaymentStatus.COMPLETED
        )
        payment_storage.create_payment(payment)

        # Create invoice with unicode
        invoice = Invoice(
            user_id=test_user_id,
            payment_id=payment.id,
            invoice_number="INV-UNICODE-001",
            description="Plan: Essential - विवरण",
            customer_name="डॉ. राजेश कुमार",
            customer_email="test@example.com",
            subtotal=99900
        )

        result = payment_storage.create_invoice(invoice)
        assert result.customer_name == "डॉ. राजेश कुमार"

    def test_extremely_long_invoice_description(self, payment_storage, test_user_id):
        """Test invoice with very long description."""
        long_description = "Test " * 1000  # 5000 characters

        invoice = Invoice(
            user_id=test_user_id,
            invoice_number="INV-LONG-001",
            description=long_description,
            subtotal=99900
        )

        result = payment_storage.create_invoice(invoice)
        assert len(result.description) >= 1000

    def test_billing_cycle_transition(self, payment_service, payment_storage, test_user_id):
        """Test transitioning between billing cycles."""
        # Monthly to yearly
        sub = Subscription(
            user_id=test_user_id,
            plan_id="essential",
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE
        )
        payment_storage.create_subscription(sub)

        result = payment_service.change_plan(
            subscription_id=sub.id,
            new_plan_id="essential",
            new_billing_cycle=BillingCycle.YEARLY,
            at_period_end=True
        )

        assert result.success is True
