from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class DangKyForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email") 

    class Meta:
        model = User
        fields = ("username", "email") 

    def __init__(self, *args, **kwargs):
        super(DangKyForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control mb-2'})