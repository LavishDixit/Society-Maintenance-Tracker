from django import forms
from .models import Complaint


class BootstrapFormMixin:
    def _add_bootstrap_classes(self):
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{existing} form-check-input'.strip()
            else:
                field.widget.attrs['class'] = f'{existing} form-control'.strip()


class ComplaintCreateForm(BootstrapFormMixin, forms.ModelForm):
    """Used by residents to raise a new complaint."""
    class Meta:
        model = Complaint
        fields = ['category', 'description', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue...'}),
            # capture='environment' opens the device's rear camera directly
            # on mobile, instead of only offering the file/gallery picker.
            'photo': forms.ClearableFileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()


class ComplaintUpdateForm(BootstrapFormMixin, forms.Form):
    """Used by admins to change status/priority, with an optional note."""
    status = forms.ChoiceField(choices=Complaint.Status.choices)
    priority = forms.ChoiceField(choices=Complaint.Priority.choices)
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional note about this update...'}),
    )
    resolution_photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
        help_text="Optional - attach an 'after' photo, sent to the resident when resolved.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()


class ComplaintFilterForm(BootstrapFormMixin, forms.Form):
    """Admin-side filters for the complaint list."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search resident, flat, or description...'})
    )
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + list(Complaint.Category.choices), required=False
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Complaint.Status.choices), required=False
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()
