from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class StyledAuthenticationForm(AuthenticationForm):
    """AuthenticationForm with Bootstrap classes applied to its widgets."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class ResidentSignUpForm(UserCreationForm):
    """
    Public registration form. Every account created here is a plain resident
    account (is_committee=False) - committee/admin access is granted later
    by an existing committee member, never through public sign-up.
    """
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)
    wing = forms.CharField(required=True, max_length=10, help_text="e.g. A, B, Tower-1")
    flat_number = forms.CharField(required=True, max_length=20, help_text="e.g. 101")
    phone_number = forms.CharField(required=False, max_length=15)

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'wing', 'flat_number', 'phone_number', 'password1', 'password2',
        )

    def clean(self):
        cleaned = super().clean()
        wing = cleaned.get('wing', '').strip()
        flat_number = cleaned.get('flat_number', '').strip()
        if wing and flat_number:
            # Same real-world guard as the DB constraint - one flat, one
            # account. This is what actually disambiguates two residents who
            # happen to share a name: the unit they live in is unique, the
            # name is not.
            if User.objects.filter(wing__iexact=wing, flat_number__iexact=flat_number).exists():
                raise forms.ValidationError(
                    f"An account already exists for {wing}-{flat_number}. "
                    "Contact your committee if this is a mistake."
                )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.wing = self.cleaned_data['wing']
        user.flat_number = self.cleaned_data['flat_number']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.is_committee = False
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
