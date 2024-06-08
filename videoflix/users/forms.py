from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from django import forms


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = "__all__"
        widgets = {
            "email": forms.EmailInput(attrs={"required": True}),
            "first_name": forms.TextInput(attrs={"required": True}),
            "last_name": forms.TextInput(attrs={"required": True}),
        }


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "address", "phone", "custom")
        # Add required=True for email, first_name, and last_name
        widgets = {
            "email": forms.EmailInput(attrs={"required": True}),
            "first_name": forms.TextInput(attrs={"required": True}),
            "last_name": forms.TextInput(attrs={"required": True}),
        }
