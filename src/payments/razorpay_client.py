"""
Razorpay Integration Client

Handles all Razorpay API interactions for:
- Subscription management
- Payment processing
- Invoice generation
- Webhook verification
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass

# Try to import razorpay SDK
try:
    import razorpay
    HAS_RAZORPAY = True
except ImportError:
    HAS_RAZORPAY = False

# Fallback to HTTP requests
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    import base64
    HAS_HTTPX = False


@dataclass
class RazorpayConfig:
    """Razorpay configuration."""
    key_id: str
    key_secret: str
    webhook_secret: Optional[str] = None
    test_mode: bool = True


class RazorpayClient:
    """
    Razorpay API client.

    Handles subscriptions, payments, and webhooks.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self, config: Optional[RazorpayConfig] = None):
        if config:
            self.config = config
        else:
            self.config = RazorpayConfig(
                key_id=os.environ.get("RAZORPAY_KEY_ID", ""),
                key_secret=os.environ.get("RAZORPAY_KEY_SECRET", ""),
                webhook_secret=os.environ.get("RAZORPAY_WEBHOOK_SECRET"),
                test_mode=os.environ.get("RAZORPAY_TEST_MODE", "true").lower() == "true",
            )

        if HAS_RAZORPAY and self.config.key_id:
            self._client = razorpay.Client(
                auth=(self.config.key_id, self.config.key_secret)
            )
        else:
            self._client = None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make HTTP request to Razorpay API."""
        url = f"{self.BASE_URL}{endpoint}"

        if HAS_HTTPX:
            auth = (self.config.key_id, self.config.key_secret)
            with httpx.Client(auth=auth) as client:
                if method == "GET":
                    response = client.get(url, params=data)
                elif method == "POST":
                    response = client.post(url, json=data)
                elif method == "PATCH":
                    response = client.patch(url, json=data)
                else:
                    return None

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    print(f"Razorpay error: {response.status_code} - {response.text}")
                    return None
        else:
            # Fallback to urllib
            import base64
            credentials = base64.b64encode(
                f"{self.config.key_id}:{self.config.key_secret}".encode()
            ).decode()

            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            }

            if method == "POST":
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode() if data else None,
                    headers=headers,
                    method="POST",
                )
            else:
                req = urllib.request.Request(url, headers=headers)

            try:
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read())
            except Exception as e:
                print(f"Razorpay error: {e}")
                return None

    # Customer Management
    def create_customer(
        self,
        name: str,
        email: str,
        contact: Optional[str] = None,
        notes: Optional[dict] = None,
    ) -> Optional[dict]:
        """Create a Razorpay customer."""
        if self._client:
            try:
                return self._client.customer.create({
                    "name": name,
                    "email": email,
                    "contact": contact,
                    "notes": notes or {},
                })
            except Exception as e:
                print(f"Error creating customer: {e}")
                return None
        else:
            return self._make_request("POST", "/customers", {
                "name": name,
                "email": email,
                "contact": contact,
                "notes": notes or {},
            })

    def get_customer(self, customer_id: str) -> Optional[dict]:
        """Get customer details."""
        if self._client:
            try:
                return self._client.customer.fetch(customer_id)
            except Exception:
                return None
        else:
            return self._make_request("GET", f"/customers/{customer_id}")

    # Plan Management
    def create_plan(
        self,
        name: str,
        amount: int,  # In paise
        currency: str = "INR",
        period: str = "monthly",  # monthly, quarterly, yearly
        interval: int = 1,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        """Create a subscription plan."""
        data = {
            "period": period,
            "interval": interval,
            "item": {
                "name": name,
                "amount": amount,
                "currency": currency,
                "description": description or name,
            },
        }

        if self._client:
            try:
                return self._client.plan.create(data)
            except Exception as e:
                print(f"Error creating plan: {e}")
                return None
        else:
            return self._make_request("POST", "/plans", data)

    def get_plan(self, plan_id: str) -> Optional[dict]:
        """Get plan details."""
        if self._client:
            try:
                return self._client.plan.fetch(plan_id)
            except Exception:
                return None
        else:
            return self._make_request("GET", f"/plans/{plan_id}")

    # Subscription Management
    def create_subscription(
        self,
        plan_id: str,
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        total_count: int = 12,  # Number of billing cycles
        quantity: int = 1,
        notes: Optional[dict] = None,
        start_at: Optional[int] = None,  # Unix timestamp
        offer_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Create a subscription."""
        data = {
            "plan_id": plan_id,
            "total_count": total_count,
            "quantity": quantity,
            "notes": notes or {},
        }

        if customer_id:
            data["customer_id"] = customer_id
        if customer_email:
            data["customer_notify"] = 1
            if not customer_id:
                # Create customer inline
                data["customer"] = {"email": customer_email}

        if start_at:
            data["start_at"] = start_at
        if offer_id:
            data["offer_id"] = offer_id

        if self._client:
            try:
                return self._client.subscription.create(data)
            except Exception as e:
                print(f"Error creating subscription: {e}")
                return None
        else:
            return self._make_request("POST", "/subscriptions", data)

    def get_subscription(self, subscription_id: str) -> Optional[dict]:
        """Get subscription details."""
        if self._client:
            try:
                return self._client.subscription.fetch(subscription_id)
            except Exception:
                return None
        else:
            return self._make_request("GET", f"/subscriptions/{subscription_id}")

    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_cycle_end: bool = True,
    ) -> Optional[dict]:
        """Cancel a subscription."""
        if self._client:
            try:
                return self._client.subscription.cancel(
                    subscription_id,
                    {"cancel_at_cycle_end": 1 if cancel_at_cycle_end else 0}
                )
            except Exception as e:
                print(f"Error cancelling subscription: {e}")
                return None
        else:
            return self._make_request(
                "POST",
                f"/subscriptions/{subscription_id}/cancel",
                {"cancel_at_cycle_end": 1 if cancel_at_cycle_end else 0}
            )

    def pause_subscription(self, subscription_id: str) -> Optional[dict]:
        """Pause a subscription."""
        if self._client:
            try:
                return self._client.subscription.pause(subscription_id)
            except Exception as e:
                print(f"Error pausing subscription: {e}")
                return None
        else:
            return self._make_request("POST", f"/subscriptions/{subscription_id}/pause")

    def resume_subscription(self, subscription_id: str) -> Optional[dict]:
        """Resume a paused subscription."""
        if self._client:
            try:
                return self._client.subscription.resume(subscription_id)
            except Exception as e:
                print(f"Error resuming subscription: {e}")
                return None
        else:
            return self._make_request("POST", f"/subscriptions/{subscription_id}/resume")

    def update_subscription(
        self,
        subscription_id: str,
        plan_id: Optional[str] = None,
        quantity: Optional[int] = None,
        schedule_change_at: str = "now",  # now or cycle_end
    ) -> Optional[dict]:
        """Update subscription (change plan or quantity)."""
        data = {"schedule_change_at": schedule_change_at}
        if plan_id:
            data["plan_id"] = plan_id
        if quantity:
            data["quantity"] = quantity

        if self._client:
            try:
                return self._client.subscription.update(subscription_id, data)
            except Exception as e:
                print(f"Error updating subscription: {e}")
                return None
        else:
            return self._make_request("PATCH", f"/subscriptions/{subscription_id}", data)

    # Order/Payment Management
    def create_order(
        self,
        amount: int,  # In paise
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[dict] = None,
    ) -> Optional[dict]:
        """Create a one-time payment order."""
        data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt or f"order_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "notes": notes or {},
        }

        if self._client:
            try:
                return self._client.order.create(data)
            except Exception as e:
                print(f"Error creating order: {e}")
                return None
        else:
            return self._make_request("POST", "/orders", data)

    def get_order(self, order_id: str) -> Optional[dict]:
        """Get order details."""
        if self._client:
            try:
                return self._client.order.fetch(order_id)
            except Exception:
                return None
        else:
            return self._make_request("GET", f"/orders/{order_id}")

    def get_payment(self, payment_id: str) -> Optional[dict]:
        """Get payment details."""
        if self._client:
            try:
                return self._client.payment.fetch(payment_id)
            except Exception:
                return None
        else:
            return self._make_request("GET", f"/payments/{payment_id}")

    def capture_payment(
        self,
        payment_id: str,
        amount: int,
        currency: str = "INR",
    ) -> Optional[dict]:
        """Capture an authorized payment."""
        if self._client:
            try:
                return self._client.payment.capture(payment_id, amount, {"currency": currency})
            except Exception as e:
                print(f"Error capturing payment: {e}")
                return None
        else:
            return self._make_request(
                "POST",
                f"/payments/{payment_id}/capture",
                {"amount": amount, "currency": currency}
            )

    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None,  # Full refund if None
        notes: Optional[dict] = None,
    ) -> Optional[dict]:
        """Refund a payment."""
        data = {"notes": notes or {}}
        if amount:
            data["amount"] = amount

        if self._client:
            try:
                return self._client.payment.refund(payment_id, data)
            except Exception as e:
                print(f"Error refunding payment: {e}")
                return None
        else:
            return self._make_request("POST", f"/payments/{payment_id}/refund", data)

    # Invoice Management
    def create_invoice(
        self,
        customer_id: str,
        line_items: list[dict],
        description: Optional[str] = None,
        due_date: Optional[int] = None,  # Unix timestamp
        sms_notify: bool = True,
        email_notify: bool = True,
    ) -> Optional[dict]:
        """Create an invoice."""
        data = {
            "type": "invoice",
            "customer_id": customer_id,
            "line_items": line_items,
            "sms_notify": 1 if sms_notify else 0,
            "email_notify": 1 if email_notify else 0,
        }

        if description:
            data["description"] = description
        if due_date:
            data["expire_by"] = due_date

        if self._client:
            try:
                return self._client.invoice.create(data)
            except Exception as e:
                print(f"Error creating invoice: {e}")
                return None
        else:
            return self._make_request("POST", "/invoices", data)

    # Webhook Verification
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
    ) -> bool:
        """Verify Razorpay webhook signature."""
        if not self.config.webhook_secret:
            return False

        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify payment signature for order payments."""
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            self.config.key_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def verify_subscription_signature(
        self,
        subscription_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify payment signature for subscription payments."""
        message = f"{payment_id}|{subscription_id}"
        expected_signature = hmac.new(
            self.config.key_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)


# Default instance
_razorpay_client: Optional[RazorpayClient] = None


def get_razorpay_client() -> RazorpayClient:
    """Get the default Razorpay client instance."""
    global _razorpay_client
    if _razorpay_client is None:
        _razorpay_client = RazorpayClient()
    return _razorpay_client
