from django.db import models


class Rule(models.Model):
    """A single rule/regulation entry that residents must follow."""
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class Contact(models.Model):
    """
    A phone-book entry - either a society committee contact (secretary,
    treasurer, guard) or a local emergency service (police, ambulance,
    mechanic, doctor, etc). Kept as one model with a category so both
    show up on a single "who do I call" page.
    """

    class Category(models.TextChoices):
        COMMITTEE = 'committee', 'Society Committee'
        EMERGENCY = 'emergency', 'Emergency Service'

    category = models.CharField(max_length=15, choices=Category.choices)
    name = models.CharField(max_length=100, help_text="e.g. 'Mr. Sharma' or 'City Police Station'")
    designation = models.CharField(max_length=100, blank=True, help_text="e.g. 'Secretary', 'Ambulance'")
    phone_number = models.CharField(max_length=20)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['category', 'designation', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
