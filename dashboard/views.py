import json

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.shortcuts import render

from complaints.models import Complaint


def is_admin(user):
    return user.is_authenticated and user.is_admin_role


@user_passes_test(is_admin, login_url='accounts:login')
def dashboard_view(request):
    complaints = Complaint.objects.all()

    by_status = list(complaints.values('status').annotate(count=Count('id')).order_by('status'))
    by_category = list(complaints.values('category').annotate(count=Count('id')).order_by('category'))

    overdue_count = sum(1 for c in complaints if c.is_overdue)
    total = complaints.count()

    status_labels_map = dict(Complaint.Status.choices)
    category_labels_map = dict(Complaint.Category.choices)

    status_chart_data = {
        'labels': [status_labels_map.get(row['status'], row['status']) for row in by_status],
        'values': [row['count'] for row in by_status],
    }
    category_chart_data = {
        'labels': [category_labels_map.get(row['category'], row['category']) for row in by_category],
        'values': [row['count'] for row in by_category],
    }

    context = {
        'total': total,
        'by_status': by_status,
        'by_category': by_category,
        'overdue_count': overdue_count,
        'status_chart_json': json.dumps(status_chart_data),
        'category_chart_json': json.dumps(category_chart_data),
    }
    return render(request, 'dashboard/dashboard.html', context)
