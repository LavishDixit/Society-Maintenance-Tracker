from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .emails import send_status_change_email
from .forms import ComplaintCreateForm, ComplaintFilterForm, ComplaintUpdateForm
from .models import Complaint


def is_admin(user):
    return user.is_authenticated and user.is_admin_role


@login_required
def redirect_after_login(request):
    if request.user.is_admin_role:
        return redirect('complaints:admin_list')
    return redirect('complaints:my_complaints')


# ---------------------------------------------------------------------------
# Resident views
# ---------------------------------------------------------------------------
@login_required
def raise_complaint(request):
    # Committee members are also residents of their own flat, so they may
    # raise complaints too - no role-based block here.
    if request.method == 'POST':
        form = ComplaintCreateForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.resident = request.user
            complaint.save()
            # First history entry so the "Open" state also shows in history.
            complaint.history.create(status=Complaint.Status.OPEN, actor=request.user, note='Complaint raised')
            messages.success(request, 'Your complaint has been submitted.')
            return redirect('complaints:my_complaints')
    else:
        form = ComplaintCreateForm()
    return render(request, 'complaints/raise_complaint.html', {'form': form})


@login_required
def my_complaints(request):
    complaints = request.user.complaints.all().prefetch_related('history')
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    # Residents may only view their own complaints; admins may view any.
    if not request.user.is_admin_role and complaint.resident_id != request.user.id:
        messages.error(request, "You don't have permission to view that complaint.")
        return redirect('complaints:my_complaints')
    return render(request, 'complaints/complaint_detail.html', {'complaint': complaint})


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------
@user_passes_test(is_admin, login_url='accounts:login')
def admin_complaint_list(request):
    filter_form = ComplaintFilterForm(request.GET or None)
    complaints = Complaint.objects.select_related('resident').all()

    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get('search'):
            term = data['search'].strip()
            complaints = complaints.filter(
                Q(resident__username__icontains=term)
                | Q(resident__flat_number__icontains=term)
                | Q(description__icontains=term)
            )
        if data.get('category'):
            complaints = complaints.filter(category=data['category'])
        if data.get('status'):
            complaints = complaints.filter(status=data['status'])
        if data.get('date_from'):
            complaints = complaints.filter(created_at__date__gte=data['date_from'])
        if data.get('date_to'):
            complaints = complaints.filter(created_at__date__lte=data['date_to'])

    complaints = list(complaints)
    # Overdue ones surface at the top, then sorted by newest.
    complaints.sort(key=lambda c: (not c.is_overdue, c.created_at), reverse=False)
    complaints.sort(key=lambda c: c.is_overdue, reverse=True)

    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preserve filters/search across pagination links.
    querystring = request.GET.copy()
    querystring.pop('page', None)

    return render(request, 'complaints/admin_list.html', {
        'page_obj': page_obj,
        'complaints': page_obj.object_list,
        'filter_form': filter_form,
        'querystring': querystring.urlencode(),
    })


@user_passes_test(is_admin, login_url='accounts:login')
def admin_complaint_update(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            status_changed = data['status'] != complaint.status
            complaint.priority = data['priority']
            if data.get('resolution_photo'):
                complaint.resolution_photo = data['resolution_photo']
            complaint.save()

            if status_changed:
                complaint.add_status_log(data['status'], actor=request.user, note=data['note'])
                send_status_change_email(complaint)
            elif data['note']:
                # Priority-only update but admin still left a note.
                complaint.history.create(
                    complaint=complaint, status=complaint.status,
                    actor=request.user, note=data['note']
                )

            messages.success(request, f'Complaint #{complaint.id} updated.')
            return redirect('complaints:admin_list')
    else:
        form = ComplaintUpdateForm(initial={
            'status': complaint.status,
            'priority': complaint.priority,
        })

    return render(request, 'complaints/admin_update.html', {
        'complaint': complaint,
        'form': form,
    })
