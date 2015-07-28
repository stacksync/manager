from django import forms
from django.forms import PasswordInput
from groups.models import StacksyncGroupUser
from users.forms import StacksyncUserForm


class StacksyncGroupUserForm(StacksyncUserForm):
    password = forms.CharField(widget=PasswordInput(), required=False)

    class Meta:
        model = StacksyncGroupUser


class RequiredFormSet(forms.models.BaseInlineFormSet):
    """
    Form makes an inline required in a django admin page
    """

    def __init__(self, *args, **kwargs):
        super(RequiredFormSet, self).__init__(*args, **kwargs)
        self.forms[0].empty_permitted = False

    def clean(self):
        """Check that at least one service has been entered."""
        super(RequiredFormSet, self).clean()
        if any(self.errors):
            return
        if not any(cleaned_data and not cleaned_data.get('DELETE', False)
                   for cleaned_data in self.cleaned_data):
            raise forms.ValidationError('At least one item required.')

