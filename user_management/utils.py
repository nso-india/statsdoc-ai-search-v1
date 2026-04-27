"""
Email utilities for user management
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)


class MOSPIEmailService:
    """Service class for sending emails via MOSPI SMTP API"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'MOSPI_SMTP_API_URL', '')
        self.auth_key = getattr(settings, 'MOSPI_SMTP_AUTH_KEY', '')
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply.nso.india@mospi.gov.in')
        
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   from_email: Optional[str] = None) -> bool:
        """
        Send email via MOSPI SMTP API
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Sender email (optional, uses default if not provided)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.api_url or not self.auth_key:
            logger.error("MOSPI SMTP API configuration missing")
            return False
            
        if not to_emails:
            logger.error("No recipient emails provided")
            return False
            
        try:
            headers = {
                'auth-key': self.auth_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                "emailData": {
                    "from": from_email or self.default_from_email,
                    "to": to_emails,
                    "subject": subject,
                    "body": body
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {', '.join(to_emails)}")
                return True
            else:
                logger.error(f"MOSPI SMTP API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email via MOSPI API: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False


# Global instance
mospi_email_service = MOSPIEmailService()


def send_verification_email_mospi(user, request=None):
    """Send email verification email using MOSPI SMTP API"""
    try:
        # Build the verification URL
        if request:
            domain = request.get_host()
        else:
            domain = getattr(settings, "DOMAIN", "localhost:8000")
        
        # Always use HTTPS for security
        protocol = "https"

        verification_url = (
            f"{protocol}://{domain}/verify-email?"
            f"email={user.email}&token={user.email_verification_token}"
        )

        # Email subject
        subject = "Verify Your Email - MOSPI Account"

        # Email context
        context = {
            "user": user,
            "verification_url": verification_url,
            "site_name": "MOSPI",
        }

        # Try to render HTML template, fallback to plain text
        try:
            html_message = render_to_string("emails/verification_email.html", context)
        except Exception as e:
            logger.warning(f"Could not render HTML template: {e}")
            # Fallback to plain text
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Verify Your Email - MOSPI</title>
</head>
<body>
    <h2>Hello {user.first_name or user.username},</h2>
    <p>Welcome to MOSPI! Please verify your email address by clicking the link below:</p>
    <p><a href="{verification_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Verify Email Address</a></p>
    <p>If the button doesn't work, copy and paste this link into your browser:</p>
    <p>{verification_url}</p>
    <p><strong>Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
    <p>If you didn't create an account with MOSPI, please ignore this email.</p>
    <p>Best regards,<br>The MOSPI Team</p>
</body>
</html>
"""

        # Send email using MOSPI API
        success = mospi_email_service.send_email(
            to_emails=[user.email],
            subject=subject,
            body=html_message
        )
        
        if success:
            logger.info(f"Verification email sent to {user.email} via MOSPI API")
        else:
            logger.error(f"Failed to send verification email to {user.email} via MOSPI API")
            
        return success

    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_welcome_email_mospi(user):
    """Send welcome email using MOSPI SMTP API"""
    try:
        subject = "Welcome to MOSPI!"

        context = {
            "user": user,
            "site_name": "MOSPI",
        }

        try:
            html_message = render_to_string("emails/welcome_email.html", context)
        except Exception as e:
            logger.warning(f"Could not render HTML template: {e}")
            # Fallback to plain text HTML
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to MOSPI!</title>
</head>
<body>
    <h2>Hello {user.first_name or user.username},</h2>
    <p>🎉 <strong>Congratulations!</strong> Your email has been successfully verified and your MOSPI account is now active.</p>
    <p>You can now access all the features of our platform:</p>
    <ul>
        <li>Upload and process documents</li>
        <li>Chat with AI assistants</li>
        <li>Analyze data and generate insights</li>
        <li>Collaborate with your team</li>
    </ul>
    <p>If you have any questions or need assistance getting started, please don't hesitate to reach out to our support team.</p>
    <p>Thank you for joining MOSPI. We're excited to see what you'll accomplish!</p>
    <p>Best regards,<br>The MOSPI Team</p>
</body>
</html>
"""

        # Send email using MOSPI API
        success = mospi_email_service.send_email(
            to_emails=[user.email],
            subject=subject,
            body=html_message
        )
        
        if success:
            logger.info(f"Welcome email sent to {user.email} via MOSPI API")
        else:
            logger.error(f"Failed to send welcome email to {user.email} via MOSPI API")
            
        return success

    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False


def send_password_reset_email_mospi(user, reset_url):
    """Send password reset email using MOSPI SMTP API"""
    try:
        subject = "Reset Your MOSPI Password"

        context = {
            "user": user,
            "reset_url": reset_url,
            "site_name": "MOSPI",
        }

        try:
            html_message = render_to_string("emails/password_reset.html", context)
        except Exception as e:
            logger.warning(f"Could not render HTML template: {e}")
            # Fallback to plain text HTML
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reset Your MOSPI Password</title>
</head>
<body>
    <h2>Hello {user.first_name or user.username},</h2>
    <p>You recently requested to reset your password for your MOSPI account.</p>
    <p>Click the button below to reset your password:</p>
    <p><a href="{reset_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
    <p>If the button doesn't work, copy and paste this link into your browser:</p>
    <p>{reset_url}</p>
    <p><strong>Important:</strong> This password reset link will expire in 1 hour for security reasons.</p>
    <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
    <p>Best regards,<br>The MOSPI Team</p>
</body>
</html>
"""

        # Send email using MOSPI API
        success = mospi_email_service.send_email(
            to_emails=[user.email],
            subject=subject,
            body=html_message
        )
        
        if success:
            logger.info(f"Password reset email sent to {user.email} via MOSPI API")
        else:
            logger.error(f"Failed to send password reset email to {user.email} via MOSPI API")
            
        return success

    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False


def send_verification_email(user, request=None):
    """Send email verification email to user using MOSPI API with fallback"""
    try:
        # Try MOSPI API first
        success = send_verification_email_mospi(user, request)
        if success:
            return True
        
        # Fallback to Django's built-in email system
        logger.warning("MOSPI API failed, falling back to Django email system")
        
        # Build the verification URL - always use HTTPS
        if request:
            domain = request.get_host()
        else:
            domain = getattr(settings, "DOMAIN", "localhost:8000")
        
        # Always use HTTPS for security
        protocol = "https"

        verification_url = (
            f"{protocol}://{domain}/verify-email?"
            f"email={user.email}&token={user.email_verification_token}"
        )

        # Email subject
        subject = "Verify Your Email - MOSPI Account"

        # Email context
        context = {
            "user": user,
            "verification_url": verification_url,
            "site_name": "MOSPI",
        }

        # Try to render HTML template, fallback to plain text
        try:
            html_message = render_to_string("emails/verification_email.html", context)
            plain_message = strip_tags(html_message)
        except Exception:
            # Fallback to plain text if template doesn't exist
            plain_message = f"""
Hello {user.first_name or user.username},

Welcome to MOSPI! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account with us, please ignore this email.

Best regards,
The MOSPI Team
"""
            html_message = None

        # Send email using Django's system
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {user.email} via Django fallback")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_welcome_email(user):
    """Send welcome email after successful verification using MOSPI API with fallback"""
    try:
        # Try MOSPI API first
        success = send_welcome_email_mospi(user)
        if success:
            return True
        
        # Fallback to Django's built-in email system
        logger.warning("MOSPI API failed, falling back to Django email system")
        
        subject = "Welcome to MOSPI!"

        context = {
            "user": user,
            "site_name": "MOSPI",
        }

        try:
            html_message = render_to_string("emails/welcome_email.html", context)
            plain_message = strip_tags(html_message)
        except Exception:
            # Fallback to plain text
            plain_message = f"""
Hello {user.first_name or user.username},

Welcome to MOSPI! Your account has been successfully verified.

You can now log in and start using our platform.

Best regards,
The MOSPI Team
"""
            html_message = None

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user.email} via Django fallback")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False
