"""
Email notification helpers.

Uses Django's standard email machinery, configured in settings.py to route
through SendGrid's SMTP relay in production and print to console in local
dev. Kept in one module so both the complaints app and notices app call the
same thin wrapper.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage, send_mail

logger = logging.getLogger(__name__)


def _safe_send(subject, message, to_email):
    if not to_email:
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception:
        # Never let an email failure break the user-facing request/response
        # cycle - log it and move on.
        logger.exception("Failed to send email to %s", to_email)


def send_status_change_email(complaint):
    resident = complaint.resident
    if not resident.email:
        return

    subject = f"Update on your complaint #{complaint.id}"
    message = (
        f"Hi {resident.get_full_name() or resident.username},\n\n"
        f"Your complaint \"{complaint.get_category_display()}\" (#{complaint.id}) "
        f"has been updated to: {complaint.get_status_display()}.\n\n"
        f"Description: {complaint.description}\n\n"
    )
    if complaint.status == complaint.Status.RESOLVED:
        message += "This complaint is now closed. Thank you for your patience.\n\n"
        if complaint.resolution_photo:
            message += "A photo of the completed work is attached.\n\n"
    message += "- Society Maintenance Tracker"

    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[resident.email],
        )
        # Attach the "after" photo only when resolving and one was provided.
        if complaint.status == complaint.Status.RESOLVED and complaint.resolution_photo:
            try:
                complaint.resolution_photo.open('rb')
                filename = complaint.resolution_photo.name.rsplit('/', 1)[-1]
                email.attach(filename, complaint.resolution_photo.read())
            finally:
                complaint.resolution_photo.close()
        email.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send status-change email to %s", resident.email)


def send_important_notice_email(notice, recipient_emails):
    subject = f"[Important Notice] {notice.title}"
    message = f"{notice.body}\n\n- Society Maintenance Tracker"
    for email in recipient_emails:
        _safe_send(subject, message, email)
