from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'avatar_id', 'creation_date')
    list_filter = ('id', 'user', 'name', 'creation_date')
    list_display_links = ('name',)
    search_fields = ('name', 'user__username')
    ordering = ('-creation_date',)
    readonly_fields = ('id', 'creation_date',)
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description', 'avatar_id', 'user', 'creation_date')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user',)
        return self.readonly_fields

admin.site.register(Profile, ProfileAdmin)