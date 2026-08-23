from django import forms
from .models import Rule, Contact


class BootstrapFormMixin:
    def _add_bootstrap_classes(self):
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RuleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Rule
        fields = ['order', 'title', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['category', 'name', 'designation', 'phone_number', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()
