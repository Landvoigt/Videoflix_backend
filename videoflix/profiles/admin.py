from django.contrib import admin

from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'active', 'user', 'avatar_id', 'created_at')
    list_filter = ('id', 'user', 'name', 'created_at')
    list_display_links = ('name',)
    search_fields = ('name', 'user__username')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'active', 'created_at',)
    fieldsets = (
        (None, {
            'fields': ('id', 'active', 'name', 'description', 'avatar_id', 'user', 'created_at', 'liked_list', 'view_list')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user',)
        return self.readonly_fields

admin.site.register(Profile, ProfileAdmin)