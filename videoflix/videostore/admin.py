from django.contrib import admin
from .models import Video


class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title','category','video_file', 'description','age', 'resolution','release_date','created_at','hls_playlist')

admin.site.register(Video, VideoAdmin)
