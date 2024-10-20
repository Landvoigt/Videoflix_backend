import os
from google.cloud import storage
from django.conf import settings
from datetime import date
from django.db import models
import logging


logger = logging.getLogger(__name__)


AGE_CHOICES = [
    ("0", "Ohne Altersbeschränkung"),
    ("6", "Ab 6 Jahren"),
    ("12", "Ab 12 Jahren"),
    ("16", "Ab 16 Jahren"),
    ("18", "Ab 18 Jahren"),
]

RELEASE_CHOICES = [
    ('2019', "2019"),
    ('2020', "2020"),
    ('2021', "2021"),
    ('2022', "2022"),
    ('2023', "2023"),
    ('2024', "2024"),   
]

CATEGORY_CHOICES = [
    ("serie", "serie"),
    ("film", "film")
]

RESOLUTION_CHOICES = [
    ("HD", "HD"),
    ("4K", "4K")
]


class Video(models.Model):
    created_at = models.DateField(default=date.today)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=500)
    video_file = models.FileField(upload_to="videos", blank=True, null=True)
    hls_playlist = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=50, blank=True, null=True)
    age = models.CharField(choices=AGE_CHOICES,max_length=10, blank=True, null=True) 
    resolution = models.CharField(choices=RESOLUTION_CHOICES,max_length=20, blank=True, null=True)
    release_date = models.CharField(choices=RELEASE_CHOICES,max_length=4, blank=True, null=True)
    video_duration = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.video_file and not self.hls_playlist:
            video_name = os.path.splitext(os.path.basename(self.video_file.name))[0]
            gcs_url = f"https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/hls/{video_name}/master.m3u8"
            self.hls_playlist = gcs_url
       
        if self.video_file:
            self.video_file.name = os.path.basename(self.video_file.name)
    
        super().save(*args, **kwargs)

        if self.video_file:
            self.upload_text_to_gcs()


def upload_text_to_gcs(self):
    gcs_client = create_gcs_client()
    gcs_bucket = gcs_client.bucket(settings.GS_BUCKET_NAME)
    gcs_base_path = get_gcs_base_path(self.video_file.name)
    self.video_duration = self.get_video_duration_if_needed() 

    paths_and_contents = {
        'hlsPlaylist.txt': self.hls_playlist or "",
        'title.txt': self.title or "",
        'description.txt': self.description or "",
        'category.txt': self.category or "",
        'age.txt': self.age or "0",
        'resolution.txt': self.resolution or "HD",
        'release_date.txt': self.release_date or "2020",
        'video_duration.txt': self.video_duration or "00:00:00"
    }
    upload_files_to_gcs(gcs_bucket, gcs_base_path, paths_and_contents)


def create_gcs_client():  
    return storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)


def get_gcs_base_path(video_file_name):
    video_name = os.path.splitext(os.path.basename(video_file_name))[0]
    return f"text/{video_name}/"


def get_video_duration_if_needed(self):
    if not self.video_duration:
        from .signals import get_video_duration
        return get_video_duration(self)
    return self.video_duration


def upload_files_to_gcs(gcs_bucket, gcs_base_path, paths_and_contents):
    for filename, content in paths_and_contents.items():
        gcs_path = os.path.join(gcs_base_path, filename)
        _upload_to_gcs(gcs_bucket, gcs_path, content)


def _upload_to_gcs(gcs_bucket, gcs_path, content):
    blob = gcs_bucket.blob(gcs_path)
    print(f"Uploading to GCS path: {gcs_path} with content: {content}")
    blob.upload_from_string(content)


def __str__(self):
        return self.title