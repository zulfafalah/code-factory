# test_email.py
import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def test_email_configuration():
    try:
        # Create email message
        email = EmailMessage(
            subject="Test Email Configuration",
            body="""
            Hello,
            
            This is a test email to verify the email configuration is working.
            
            Best regards,
            Your Application
            """,
            from_email=settings.EMAIL_HOST_USER,
            to=["yuksri99@gmail.com"],
            reply_to=[settings.EMAIL_HOST_USER],
        )

        # Print configuration for debugging
        logger.info("Email Configuration:")
        logger.info(f"Backend: {settings.EMAIL_BACKEND}")  # noqa: G004
        logger.info(f"Host: {settings.EMAIL_HOST}")  # noqa: G004
        logger.info(f"Port: {settings.EMAIL_PORT}")
        logger.info(f"TLS: {settings.EMAIL_USE_TLS}")
        logger.info(f"From Email: {settings.EMAIL_HOST_USER}")

        # Attempt to send email
        result = email.send(fail_silently=False)

        if result == 1:
            logger.info("Email sent successfully!")
            return True, "Email sent successfully!"
        else:
            logger.error(f"Failed to send email. Result: {result}")
            return False, f"Failed to send email. Result: {result}"

    except Exception as e:
        error_message = f"Error sending email: {str(e)}"
        logger.error(error_message)
        return False, error_message
