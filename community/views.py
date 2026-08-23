from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm, RuleForm
from .models import Contact, Rule


def is_committee(user):
    return user.is_authenticated and user.is_committee


# ---------------------------------------------------------------------------
# Rules & Regulations - readable by everyone, editable by committee only
# ---------------------------------------------------------------------------
@login_required
def rules_list(request):
    rules = Rule.objects.all()
    return render(request, 'community/rules_list.html', {'rules': rules})


@user_passes_test(is_committee, login_url='accounts:login')
def rule_add(request):
    if request.method == 'POST':
        form = RuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rule added.')
            return redirect('community:rules_list')
    else:
        form = RuleForm()
    return render(request, 'community/rule_form.html', {'form': form, 'heading': 'Add a Rule'})


@user_passes_test(is_committee, login_url='accounts:login')
def rule_edit(request, pk):
    rule = get_object_or_404(Rule, pk=pk)
    if request.method == 'POST':
        form = RuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rule updated.')
            return redirect('community:rules_list')
    else:
        form = RuleForm(instance=rule)
    return render(request, 'community/rule_form.html', {'form': form, 'heading': 'Edit Rule'})


@user_passes_test(is_committee, login_url='accounts:login')
def rule_delete(request, pk):
    rule = get_object_or_404(Rule, pk=pk)
    rule.delete()
    messages.success(request, 'Rule removed.')
    return redirect('community:rules_list')


# ---------------------------------------------------------------------------
# Committee / Emergency contacts - readable by everyone, editable by
# committee only
# ---------------------------------------------------------------------------
@login_required
def contacts_list(request):
    committee_contacts = Contact.objects.filter(category=Contact.Category.COMMITTEE)
    emergency_contacts = Contact.objects.filter(category=Contact.Category.EMERGENCY)
    return render(request, 'community/contacts_list.html', {
        'committee_contacts': committee_contacts,
        'emergency_contacts': emergency_contacts,
    })


@user_passes_test(is_committee, login_url='accounts:login')
def contact_add(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact added.')
            return redirect('community:contacts_list')
    else:
        form = ContactForm()
    return render(request, 'community/contact_form.html', {'form': form, 'heading': 'Add a Contact'})


@user_passes_test(is_committee, login_url='accounts:login')
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact updated.')
            return redirect('community:contacts_list')
    else:
        form = ContactForm(instance=contact)
    return render(request, 'community/contact_form.html', {'form': form, 'heading': 'Edit Contact'})


@user_passes_test(is_committee, login_url='accounts:login')
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.delete()
    messages.success(request, 'Contact removed.')
    return redirect('community:contacts_list')
