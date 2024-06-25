from django.contrib import admin

from .models import EmailVerificationToken


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "key", "created_at")
    search_fields = ("user", "key", "created_at")
    readonly_fields = ("user", "created_at")
    fieldsets = (
        (
            None,
            {"fields": ("key", "created_at", "user")},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user",)
        return self.readonly_fields