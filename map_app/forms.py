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

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Tên", max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Họ", max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']