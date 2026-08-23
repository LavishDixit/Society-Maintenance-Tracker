from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model.

    Every user is fundamentally a resident (has a wing + flat number).
    `is_committee` is an *additive* permission flag, not an exclusive role -
    a committee member is still a resident of their own flat and can raise
    complaints for it, while also getting access to the admin tools.

    `role` is kept only for backward compatibility with the original
    migration; it is no longer used to decide permissions (see
    `is_admin_role` / `is_resident` below, which are now driven by
    `is_committee`).
    """

    class Role(models.TextChoices):
        RESIDENT = 'resident', 'Resident'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.RESIDENT)

    wing = models.CharField(max_length=10, blank=True, help_text="e.g. A, B, Tower-1")
    flat_number = models.CharField(max_length=20, blank=True, help_text="e.g. 101")
    phone_number = models.CharField(max_length=15, blank=True)

    is_committee = models.BooleanField(
        default=False,
        help_text="Committee/admin member. Grants access to admin tools in "
                   "addition to this person's normal resident account.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['wing', 'flat_number'],
                condition=models.Q(flat_number__gt=''),
                name='unique_wing_flat_when_set',
            )
        ]

    @property
    def is_resident(self):
        # Every account is a resident account.
        return True

    @property
    def is_admin_role(self):
        # Kept as the permission-check name used throughout views/templates;
        # backed by the additive `is_committee` flag rather than an
        # exclusive role.
        return self.is_committee

    @property
    def display_name(self):
        full = self.get_full_name()
        name = full if full else self.username
        if self.wing or self.flat_number:
            unit = f"{self.wing}-{self.flat_number}" if self.wing else self.flat_number
            return f"{name} ({unit})"
        return name

    def __str__(self):
        tag = 'committee' if self.is_committee else 'resident'
        return f"{self.username} ({tag})"
