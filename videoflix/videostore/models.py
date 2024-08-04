
import os
from google.cloud import storage
from django.conf import settings
from datetime import date
from django.db import models

class Video(models.Model):
    created_at = models.DateField(default=date.today)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=500)
    video_file = models.FileField(upload_to="videos", blank=True, null=True)
    hls_playlist = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.video_file and not self.hls_playlist:
            video_name = os.path.splitext(os.path.basename(self.video_file.name))[0]
            gcs_url = f"https://storage.googleapis.com/videoflix-storage/hls/{video_name}/master.m3u8"
            self.hls_playlist = gcs_url

        if self.video_file:
            self.video_file.name = os.path.basename(self.video_file.name)

        super().save(*args, **kwargs)

        # Upload title, description, and category to GCS
        if self.video_file:
            self.upload_text_to_gcs()

    def upload_text_to_gcs(self):
        gcs_client = storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)
        gcs_bucket = gcs_client.bucket(settings.GS_BUCKET_NAME)

        # Extract base name without extension
        video_name = os.path.splitext(os.path.basename(self.video_file.name))[0]

        # Define the paths for title, description, and category
        gcs_base_path = f"text/{video_name}/"
        title_path = os.path.join(gcs_base_path, 'title.txt')
        description_path = os.path.join(gcs_base_path, 'description.txt')
        category_path = os.path.join(gcs_base_path, 'category.txt')

        # Debugging output
        print(f"Uploading files to GCS:\n Title path: {title_path}\n Description path: {description_path}\n Category path: {category_path}")
        print(f"Title content: {self.title}\n Description content: {self.description}\n Category content: {self.category}")

        # Create or update the files in GCS
        self._upload_to_gcs(gcs_bucket, title_path, self.title or "")
        self._upload_to_gcs(gcs_bucket, description_path, self.description or "")
        self._upload_to_gcs(gcs_bucket, category_path, self.category or "")

    def _upload_to_gcs(self, bucket, path, content):
        blob = bucket.blob(path)
        # Debugging output
        print(f"Uploading to GCS path: {path} with content: {content}")
        blob.upload_from_string(content)

    def __str__(self):
        return self.title
