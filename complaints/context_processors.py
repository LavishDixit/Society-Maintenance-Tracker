from .models import Complaint


def overdue_count(request):
    """
    Makes the current overdue complaint count available to every template
    (used for the nav badge), without every view having to fetch it.
    Only computed for logged-in admins - a cheap no-op otherwise.
    """
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and getattr(user, 'is_admin_role', False):
        complaints = Complaint.objects.exclude(status=Complaint.Status.RESOLVED)
        count = sum(1 for c in complaints if c.is_overdue)
        return {'nav_overdue_count': count}
    return {'nav_overdue_count': 0}
