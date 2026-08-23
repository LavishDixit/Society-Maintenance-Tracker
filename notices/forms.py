from django import forms
from accounts.models import User
from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'body', 'is_important', 'target_type', 'target_wing', 'target_resident']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_resident'].queryset = User.objects.all().order_by('wing', 'flat_number')
        self.fields['target_resident'].required = False
        self.fields['target_wing'].required = False
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        target_type = cleaned.get('target_type')
        if target_type == Notice.TargetType.WING and not cleaned.get('target_wing'):
            self.add_error('target_wing', 'Enter a wing when targeting a specific wing.')
        if target_type == Notice.TargetType.RESIDENT and not cleaned.get('target_resident'):
            self.add_error('target_resident', 'Choose a resident when targeting a specific resident.')
        return cleaned
