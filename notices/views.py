from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from accounts.models import User
from complaints.emails import send_important_notice_email
from .forms import NoticeForm
from .models import Notice


def is_admin(user):
    return user.is_authenticated and user.is_admin_role


@login_required
def notice_board(request):
    """Visible to everyone, filtered to notices addressed to this viewer."""
    notices = [n for n in Notice.objects.all() if n.is_visible_to(request.user)]
    return render(request, 'notices/notice_board.html', {'notices': notices})


def _recipient_emails_for(notice):
    """Resolve the resident emails a notice's targeting should reach."""
    if notice.target_type == Notice.TargetType.RESIDENT:
        if notice.target_resident and notice.target_resident.email:
            return [notice.target_resident.email]
        return []
    if notice.target_type == Notice.TargetType.WING:
        return list(
            User.objects.filter(wing__iexact=notice.target_wing)
            .exclude(email='')
            .values_list('email', flat=True)
        )
    # ALL
    return list(User.objects.exclude(email='').values_list('email', flat=True))


@user_passes_test(is_admin, login_url='accounts:login')
def post_notice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.author = request.user
            notice.save()

            if notice.is_important:
                send_important_notice_email(notice, _recipient_emails_for(notice))

            messages.success(request, 'Notice posted.')
            return redirect('notices:notice_board')
    else:
        form = NoticeForm()
    return render(request, 'notices/post_notice.html', {'form': form})
