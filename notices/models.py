from django.conf import settings
from django.db import models


class Notice(models.Model):
    """A notice posted by a committee member to the society notice board."""

    class TargetType(models.TextChoices):
        ALL = 'all', 'All Residents'
        WING = 'wing', 'Specific Wing'
        RESIDENT = 'resident', 'Specific Resident'

    title = models.CharField(max_length=200)
    body = models.TextField()
    is_important = models.BooleanField(default=False, help_text="Important notices are pinned to the top")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    target_type = models.CharField(max_length=10, choices=TargetType.choices, default=TargetType.ALL)
    target_wing = models.CharField(max_length=10, blank=True, help_text="Required when target is 'Specific Wing'")
    target_resident = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='targeted_notices', help_text="Required when target is 'Specific Resident'"
    )

    class Meta:
        # Pinned (important) notices first, then newest first.
        ordering = ['-is_important', '-created_at']

    def __str__(self):
        return self.title

    def is_visible_to(self, user):
        """
        Committee members see every notice regardless of targeting (they're
        managing the board); everyone else only sees notices addressed to
        them - the whole society, their wing, or them personally.
        """
        if getattr(user, 'is_committee', False):
            return True
        if self.target_type == self.TargetType.ALL:
            return True
        if self.target_type == self.TargetType.WING:
            return bool(user.wing) and user.wing.lower() == self.target_wing.lower()
        if self.target_type == self.TargetType.RESIDENT:
            return self.target_resident_id == user.id
        return False
