from django import forms
from django.forms import ModelForm, PasswordInput
from users.models import StacksyncUser


class StacksyncUserForm(ModelForm):
    password = forms.CharField(widget=PasswordInput(), required=False)
    quota_limit = forms.IntegerField(required=False)

    def clean_field(self):
        data = self.cleaned_data['password']
        if not data:
            data = 'testpass'

        return data

    class Meta:
        model = StacksyncUser
