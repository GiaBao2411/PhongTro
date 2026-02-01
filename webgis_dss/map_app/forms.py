from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class DangKyForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email") # Bắt buộc nhập Email

    class Meta:
        model = User
        fields = ("username", "email") # Chỉ hiện tên đăng nhập và email

    # Thêm class CSS của Bootstrap để form đẹp hơn
    def __init__(self, *args, **kwargs):
        super(DangKyForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control mb-2'})