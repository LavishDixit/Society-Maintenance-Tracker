from django import template

register = template.Library()

_STATUS_STAMP = {
    'open': 'stamp-open',
    'in_progress': 'stamp-inprogress',
    'resolved': 'stamp-resolved',
}

_PRIORITY_STAMP = {
    'low': 'stamp-priority-low',
    'medium': 'stamp-priority-medium',
    'high': 'stamp-priority-high',
}

_CATEGORY_ICON = {
    'plumbing': '🔧',
    'electrical': '⚡',
    'cleaning': '🧹',
    'security': '🛡️',
    'lift': '🛗',
    'parking': '🚗',
    'other': '📋',
}


@register.filter
def status_stamp(value):
    """Maps a Complaint.Status value to its stamp CSS class."""
    return _STATUS_STAMP.get(value, 'stamp-open')


@register.filter
def priority_stamp(value):
    """Maps a Complaint.Priority value to its stamp CSS class."""
    return _PRIORITY_STAMP.get(value, 'stamp-priority-low')


@register.filter
def category_icon(value):
    """Maps a Complaint.Category value to a small representative icon."""
    return _CATEGORY_ICON.get(value, '📋')
