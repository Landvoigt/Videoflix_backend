
import os
from google.cloud import storage
from django.conf import settings
from datetime import date
from django.db import models
from moviepy.editor import VideoFileClip 


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
            
        if self.video_file:
            self.video_duration = self.get_video_duration() 

        super().save(*args, **kwargs)

        if self.video_file:
            self.upload_text_to_gcs()
    
            
    def get_video_duration(self):
        video_path = self.video_file.path
        clip = VideoFileClip(video_path)
        duration_in_seconds = clip.duration 
        clip.close() 
        return str(int(duration_in_seconds // 3600)).zfill(2) + ':' + str(int((duration_in_seconds % 3600) // 60)).zfill(2) + ':' + str(int(duration_in_seconds % 60)).zfill(2)

    
    def upload_text_to_gcs(self):
        gcs_client = storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)
        gcs_bucket = gcs_client.bucket(settings.GS_BUCKET_NAME)

        video_name = os.path.splitext(os.path.basename(self.video_file.name))[0]
        gcs_base_path = f"text/{video_name}/"

        hls_playlist_url = os.path.join(gcs_base_path, 'hlsPlaylist.txt')
        title_path = os.path.join(gcs_base_path, 'title.txt')
        description_path = os.path.join(gcs_base_path, 'description.txt')
        category_path = os.path.join(gcs_base_path, 'category.txt')
        age_path = os.path.join(gcs_base_path, 'age.txt')
        resolution_path = os.path.join(gcs_base_path, 'resolution.txt')
        release_date_path = os.path.join(gcs_base_path, 'release_date.txt')
        video_duration_path = os.path.join(gcs_base_path, 'video_duration.txt') 

        self._upload_to_gcs(gcs_bucket, hls_playlist_url, self.hls_playlist or "")
        self._upload_to_gcs(gcs_bucket, title_path, self.title or "")
        self._upload_to_gcs(gcs_bucket, description_path, self.description or "")
        self._upload_to_gcs(gcs_bucket, category_path, self.category or "")
        self._upload_to_gcs(gcs_bucket, age_path, self.age or "0") 
        self._upload_to_gcs(gcs_bucket, resolution_path, self.resolution or "HD")
        self._upload_to_gcs(gcs_bucket, release_date_path, self.release_date or "2020")
        self._upload_to_gcs(gcs_bucket, video_duration_path, self.video_duration or "00:00:00")

    def _upload_to_gcs(self, bucket, path, content):
        blob = bucket.blob(path)
        print(f"Uploading to GCS path: {path} with content: {content}")
        blob.upload_from_string(content)

    def __str__(self):
        return self.title