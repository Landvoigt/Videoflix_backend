
import os
import logging
from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import django_rq
from django.conf import settings
from google.cloud import storage
import shutil

logger = logging.getLogger(__name__)



@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created:
        queue = django_rq.get_queue('default', autocommit=True)
        logger.info(f"Enqueuing video id {instance.id} for conversion")
        print(f"Enqueuing video id {instance.id} for conversion")

        video_name, _ = os.path.splitext(os.path.basename(instance.video_file.path))

        from .tasks import convert_to_hls
        queue.enqueue(convert_to_hls, instance.id, video_name=video_name)
        print(f"Video enqueued for HLS conversion: ID {instance.id}, Name {video_name}")
        logger.debug(f"Video enqueued for HLS conversion: ID {instance.id}, Name {video_name}")
        


                
@receiver(post_delete, sender=Video)
def delete_django_admin_video(sender, instance, **kwargs):
    if instance.video_file:
        video_path = instance.video_file.path   
        video_name = os.path.splitext(os.path.basename(video_path))[0] 
        video_dir = os.path.join(os.path.dirname(video_path), video_name)

        if os.path.isfile(video_path):
            try:
                os.remove(video_path)
                logger.info(f"Deleted video file: {video_path}")
            except Exception as e:
                logger.error(f"Error deleting video file {video_path}: {e}")

        if os.path.isdir(video_dir):
            try:
                shutil.rmtree(video_dir)
                logger.info(f"Deleted video directory: {video_dir}")
            except Exception as e:
                logger.error(f"Error deleting directory {video_dir}: {e}")


               

@receiver(post_delete, sender=Video)
def delete_gcs_video(sender, instance, **kwargs):
    try:
        logger.info(f"Connecting to Google Cloud Storage with credentials: {settings.GS_CREDENTIALS}")
        client = storage.Client(credentials=settings.GS_CREDENTIALS)
        # bucket = client.bucket('videoflix-videos') 
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        
        _, filename = os.path.split(instance.video_file.name)
        base_path = os.path.splitext(filename)[0]
        
        folder_path = f"hls/{base_path}/"

        blobs_to_delete = bucket.list_blobs(prefix=folder_path)
        
        for blob in blobs_to_delete:
            blob.delete()
            logger.info(f"Deleted {blob.name} from Google Cloud Storage")
        
        logger.info(f"Deleted all files in folder {folder_path} from Google Cloud Storage")

    except Exception as e:
        logger.error(f"Error deleting HLS files from Google Cloud Storage: {e}")



