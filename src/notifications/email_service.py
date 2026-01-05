"""
Email Service - High-level email utilities for common operations

Provides templates and helpers for:
- Email verification
- Password reset
- MFA codes
- System alerts
- Notifications
"""

import logging
from typing import Optional
from datetime import datetime

from .email import SendGridEmail, EmailResult

logger = logging.getLogger(__name__)


class EmailService:
    """
    High-level email service for common email operations.
    """

    def __init__(self, provider: Optional[SendGridEmail] = None):
        self.provider = provider or SendGridEmail()

    async def send_verification_email(
        self,
        to: str,
        user_name: str,
        verification_token: str,
        base_url: str = "https://app.docassist.in",
    ) -> EmailResult:
        """
        Send email verification link.

        Args:
            to: Recipient email
            user_name: User's name
            verification_token: Verification token
            base_url: Base URL for verification link

        Returns:
            EmailResult
        """
        verification_url = f"{base_url}/auth/verify-email?token={verification_token}"

        subject = "Verify Your DocAssist Account"

        body = f"""
Hello {user_name},

Welcome to DocAssist Dora! Please verify your email address to activate your account.

Click the link below to verify your email:
{verification_url}

This link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The DocAssist Team
"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066CC; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 30px; background-color: #0066CC;
                   color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to DocAssist</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Welcome to DocAssist Dora! Please verify your email address to activate your account.</p>
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #0066CC;">{verification_url}</p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <p style="margin-top: 30px; color: #666;">
                If you didn't create this account, please ignore this email.
            </p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.utcnow().year} DocAssist. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        return await self.provider.send(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
        )

    async def send_password_reset_email(
        self,
        to: str,
        user_name: str,
        reset_token: str,
        base_url: str = "https://app.docassist.in",
    ) -> EmailResult:
        """
        Send password reset link.

        Args:
            to: Recipient email
            user_name: User's name
            reset_token: Password reset token
            base_url: Base URL for reset link

        Returns:
            EmailResult
        """
        reset_url = f"{base_url}/auth/reset-password?token={reset_token}"

        subject = "Reset Your DocAssist Password"

        body = f"""
Hello {user_name},

You requested to reset your password for your DocAssist account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact support if you're concerned about your account security.

Best regards,
The DocAssist Team
"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066CC; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 30px; background-color: #DC3545;
                   color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .warning {{ background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>You requested to reset your password for your DocAssist account.</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #0066CC;">{reset_url}</p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <div class="warning">
                <strong>Security Notice:</strong> If you didn't request a password reset,
                please ignore this email or contact support if you're concerned about your account security.
            </div>
        </div>
        <div class="footer">
            <p>&copy; {datetime.utcnow().year} DocAssist. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        return await self.provider.send(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
        )

    async def send_mfa_code_email(
        self,
        to: str,
        user_name: str,
        code: str,
    ) -> EmailResult:
        """
        Send MFA verification code.

        Args:
            to: Recipient email
            user_name: User's name
            code: MFA code

        Returns:
            EmailResult
        """
        subject = "Your DocAssist Verification Code"

        body = f"""
Hello {user_name},

Your verification code is: {code}

This code will expire in 5 minutes.

If you didn't request this code, please ignore this email.

Best regards,
The DocAssist Team
"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066CC; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; text-align: center; }}
        .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px;
                 color: #0066CC; padding: 20px; background-color: white;
                 border-radius: 5px; display: inline-block; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Verification Code</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Your verification code is:</p>
            <div class="code">{code}</div>
            <p><strong>This code will expire in 5 minutes.</strong></p>
            <p style="margin-top: 30px; color: #666;">
                If you didn't request this code, please ignore this email.
            </p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.utcnow().year} DocAssist. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        return await self.provider.send(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
        )

    async def send_alert_email(
        self,
        to: str,
        alert_title: str,
        alert_message: str,
        alert_data: Optional[dict] = None,
    ) -> EmailResult:
        """
        Send system alert email.

        Args:
            to: Recipient email
            alert_title: Alert title
            alert_message: Alert message
            alert_data: Additional alert data

        Returns:
            EmailResult
        """
        subject = f"[ALERT] {alert_title}"

        data_html = ""
        if alert_data:
            data_html = "<h3>Details:</h3><ul>"
            for key, value in alert_data.items():
                data_html += f"<li><strong>{key}:</strong> {value}</li>"
            data_html += "</ul>"

        body = f"""
SYSTEM ALERT

{alert_title}

{alert_message}

Timestamp: {datetime.utcnow().isoformat()}
"""

        if alert_data:
            body += "\nDetails:\n"
            for key, value in alert_data.items():
                body += f"- {key}: {value}\n"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Courier New', monospace; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #DC3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .alert {{ background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 15px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ SYSTEM ALERT</h1>
        </div>
        <div class="content">
            <h2>{alert_title}</h2>
            <div class="alert">
                <p>{alert_message}</p>
            </div>
            {data_html}
            <p style="margin-top: 20px; color: #666;">
                <strong>Timestamp:</strong> {datetime.utcnow().isoformat()}
            </p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.utcnow().year} DocAssist. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        return await self.provider.send(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
        )


# Global instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
