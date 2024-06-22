from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _

from rest_framework.authtoken.models import Token


class CustomUserAdmin(DefaultUserAdmin):   # Update for default Django User Model in admin panel
    def token(self, obj):
        try:
            token = Token.objects.get(user=obj)
            return token.key
        except Token.DoesNotExist:
            return 'No Token'
    token.short_description = 'Token'

    fieldsets = (
        (_("Login Data"), {"fields": ("email", "password")}),
        ('', {'fields': ()}),
        (None, {'fields': ('username', 'token')}),
        (_("Personal Data"), {"fields": ("first_name", "last_name")}),
        (_("Dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    readonly_fields = ('token',)
    list_display = ("email", "username", "last_login", "date_joined", "is_active", "is_superuser")
    search_fields = ("email", "username", "first_name", "last_name")


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)