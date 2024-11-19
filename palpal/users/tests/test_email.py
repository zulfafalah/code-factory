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
        logger.info(f"Port: {settings.EMAIL_PORT}")  # noqa: G004
        logger.info(f"TLS: {settings.EMAIL_USE_TLS}")  # noqa: G004
        logger.info(f"From Email: {settings.EMAIL_HOST_USER}")  # noqa: G004

        # Attempt to send email
        result = email.send(fail_silently=False)

        if result == 1:
            logger.info("Email sent successfully!")
            return True, "Email sent successfully!"
        logger.error(f"Failed to send email. Result: {result}")  # noqa: G004
        return False, f"Failed to send email. Result: {result}"  # noqa: TRY300

    except Exception as e:  #  noqa: BLE001
        error_message = f"Error sending email: {e!s}"
        logger.error(error_message)  # noqa: TRY400
        return False, error_message
