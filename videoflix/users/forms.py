from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser

# not in use right now

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = "__all__"


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = "__all__"