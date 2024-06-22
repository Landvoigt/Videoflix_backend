from django.contrib import admin

from .models import EmailVerificationToken


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    search_fields = ('user__username', 'user__email', 'key')
