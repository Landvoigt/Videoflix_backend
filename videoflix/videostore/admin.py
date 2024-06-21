from django.contrib import admin
from .models import Video


class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title','video_file', 'description','hls_playlist','created_at')

admin.site.register(Video, VideoAdmin)
