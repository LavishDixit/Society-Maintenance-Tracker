import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone


class Complaint(models.Model):
    """
    A maintenance complaint raised by a resident.

    Current `status` and `priority` are kept as denormalized fields on the
    complaint itself for fast filtering/dashboard queries, while every change
    to status is *also* written to StatusLog below so the full history
    (who changed what, when, and why) is preserved.
    """

    class Category(models.TextChoices):
        PLUMBING = 'plumbing', 'Plumbing'
        ELECTRICAL = 'electrical', 'Electrical'
        CLEANING = 'cleaning', 'Cleaning'
        SECURITY = 'security', 'Security'
        LIFT = 'lift', 'Lift/Elevator'
        PARKING = 'parking', 'Parking'
        OTHER = 'other', 'Other'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints'
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    photo = models.ImageField(upload_to='complaints/%Y/%m/', null=True, blank=True)
    resolution_photo = models.ImageField(
        upload_to='complaints/resolved/%Y/%m/', null=True, blank=True,
        help_text="Optional 'after' photo attached when the complaint is resolved."
    )

    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} {self.get_category_display()} ({self.get_status_display()})"

    # -- Overdue detection -------------------------------------------------
    @property
    def is_overdue(self):
        """
        A complaint is overdue if it's still open (not Resolved) and has been
        sitting for longer than the configurable threshold
        (settings.OVERDUE_THRESHOLD_DAYS), counted from creation time.
        Computed on the fly rather than stored, so changing the threshold
        instantly re-evaluates every complaint without a data migration.
        """
        if self.status == self.Status.RESOLVED:
            return False
        threshold = getattr(settings, 'OVERDUE_THRESHOLD_DAYS', 5)
        age = timezone.now() - self.created_at
        return age > datetime.timedelta(days=threshold)

    @property
    def days_open(self):
        end = self.resolved_at or timezone.now()
        return (end - self.created_at).days

    def add_status_log(self, new_status, actor, note=''):
        """Update status and append an immutable history entry in one place."""
        self.status = new_status
        if new_status == self.Status.RESOLVED:
            self.resolved_at = timezone.now()
        self.save()
        return StatusLog.objects.create(
            complaint=self, status=new_status, actor=actor, note=note
        )


class StatusLog(models.Model):
    """
    Immutable audit trail entry: records every status change on a complaint
    with who did it, when, and an optional note. This is what "full status
    history" is built from - never edited or deleted, only appended to.
    """
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=15, choices=Complaint.Status.choices)
    note = models.TextField(blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Complaint #{self.complaint_id} -> {self.status} @ {self.timestamp:%Y-%m-%d %H:%M}"
