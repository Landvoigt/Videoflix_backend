import os

from datetime import date
from django.db import models


class Video(models.Model):
    created_at = models.DateField(default=date.today)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=500)
    video_file = models.FileField(upload_to="videos", blank=True, null=True)
    hls_playlist = models.CharField(max_length=200, blank=True, null=True)
    # add later
    # category = models.CharField(max_length=50, blank=True, null=True) 

    def save(self, *args, **kwargs):
        if self.video_file and not self.hls_playlist:
            video_name = os.path.splitext(os.path.basename(self.video_file.name))[0]
            gcs_url = f"https://storage.googleapis.com/videoflix-videos/hls/{video_name}/master.m3u8"
            self.hls_playlist = gcs_url

        if self.video_file:
            self.video_file.name = os.path.basename(self.video_file.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title