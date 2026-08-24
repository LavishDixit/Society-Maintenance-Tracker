"""
Email notification helpers.

Uses the Brevo HTTP API for sending emails in production.
Email failures are logged and never interrupt the user's request.
"""

import base64
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _send_email(subject, message, to_email, attachment=None):
    """Send an email using the Brevo HTTP API."""

    if not to_email:
        return

    try:
        payload = {
            "sender": {
                "email": settings.DEFAULT_FROM_EMAIL,
                "name": "Society Maintenance Tracker",
            },
            "to": [
                {
                    "email": to_email,
                }
            ],
            "subject": subject,
            "textContent": message,
        }

        # Add attachment if provided
        if attachment:
            filename, content = attachment
            encoded_content = base64.b64encode(content).decode("utf-8")

            payload["attachment"] = [
                {
                    "content": encoded_content,
                    "name": filename,
                }
            ]

        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        }

        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()
        logger.info("Email sent successfully to %s", to_email)

    except Exception:
        # Never let an email failure break the user-facing request/response
        logger.exception("Failed to send email to %s", to_email)


def send_status_change_email(complaint):
    """Send an email when the status of a complaint changes."""

    resident = complaint.resident

    if not resident.email:
        return

    subject = f"Update on your complaint #{complaint.id}"

    message = (
        f"Hi {resident.get_full_name() or resident.username},\n\n"
        f"Your complaint \"{complaint.get_category_display()}\" "
        f"(#{complaint.id}) has been updated to: "
        f"{complaint.get_status_display()}.\n\n"
        f"Description: {complaint.description}\n\n"
    )

    attachment = None

    if complaint.status == complaint.Status.RESOLVED:
        message += "This complaint is now closed. Thank you for your patience.\n\n"

        if complaint.resolution_photo:
            message += "A photo of the completed work is attached.\n\n"

            try:
                complaint.resolution_photo.open("rb")
                content = complaint.resolution_photo.read()
                filename = complaint.resolution_photo.name.rsplit("/", 1)[-1]
                attachment = (filename, content)
            finally:
                complaint.resolution_photo.close()

    message += "- Society Maintenance Tracker"

    _send_email(
        subject=subject,
        message=message,
        to_email=resident.email,
        attachment=attachment,
    )


def send_important_notice_email(notice, recipient_emails):
    """Send an important notice email to multiple recipients."""

    subject = f"[Important Notice] {notice.title}"
    message = f"{notice.body}\n\n- Society Maintenance Tracker"

    for email in recipient_emails:
        _send_email(
            subject=subject,
            message=message,
            to_email=email,
        )