import csv

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ResidentSignUpForm, StyledAuthenticationForm
from .models import User


class SignUpView(CreateView):
    """Public sign-up - always creates a resident account."""
    form_class = ResidentSignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class SocietyLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    authentication_form = StyledAuthenticationForm


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


def is_committee_member(user):
    return user.is_authenticated and user.is_committee


@user_passes_test(is_committee_member, login_url='accounts:login')
def resident_directory(request):
    """
    Searchable member directory for the committee - the in-app answer to
    "how do I quickly find someone's details". A CSV export sits alongside
    it for anyone who wants an offline copy of the same records.
    """
    query = request.GET.get('q', '').strip()
    residents = User.objects.all().order_by('wing', 'flat_number', 'username')

    if query:
        residents = residents.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(wing__icontains=query)
            | Q(flat_number__icontains=query)
            | Q(phone_number__icontains=query)
            | Q(email__icontains=query)
        )

    return render(request, 'accounts/resident_directory.html', {
        'residents': residents,
        'query': query,
    })


@user_passes_test(is_committee_member, login_url='accounts:login')
def export_residents_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="residents.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Full Name', 'Wing', 'Flat Number', 'Phone', 'Email', 'Committee Member'])
    for u in User.objects.all().order_by('wing', 'flat_number'):
        writer.writerow([
            u.username, u.get_full_name(), u.wing, u.flat_number,
            u.phone_number, u.email, 'Yes' if u.is_committee else 'No',
        ])
    return response
