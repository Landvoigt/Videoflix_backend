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



def delete_hls_folder(bucket, base_path):
    """Deletes the HLS folder and its contents."""
    hls_folder_path = f"hls/{base_path}/"
    hls_blobs_to_delete = bucket.list_blobs(prefix=hls_folder_path)
    for blob in hls_blobs_to_delete:
        blob.delete()
        logger.info(f"Deleted {blob.name} from Google Cloud Storage")
    logger.info(f"Deleted all files in folder {hls_folder_path} from Google Cloud Storage")

def delete_video_poster(bucket, base_path):
    """Deletes the video poster file."""
    poster_path = f"video-posters/{base_path}.jpg"
    poster_blob = bucket.blob(poster_path)
    if poster_blob.exists():
        poster_blob.delete()
        logger.info(f"Deleted poster {poster_path} from Google Cloud Storage")
    else:
        logger.info(f"Poster {poster_path} not found in Google Cloud Storage")

def delete_text_subfolder(bucket, base_path):
    """Deletes the text subfolder and its contents."""
    text_folder_path = f"text/{base_path}/"
    text_blobs_to_delete = bucket.list_blobs(prefix=text_folder_path)
    for blob in text_blobs_to_delete:
        blob.delete()
        logger.info(f"Deleted {blob.name} from Google Cloud Storage")
    logger.info(f"Deleted all files in subfolder {text_folder_path} from Google Cloud Storage")

def delete_myfilms_subfolder(bucket, base_path):
    """Deletes the myFilms subfolder and its contents."""
    myfilms_folder_path = f"myFilms/{base_path}/"
    myfilms_blobs_to_delete = bucket.list_blobs(prefix=myfilms_folder_path)
    for blob in myfilms_blobs_to_delete:
        blob.delete()
        logger.info(f"Deleted {blob.name} from Google Cloud Storage")
    logger.info(f"Deleted all files in subfolder {myfilms_folder_path} from Google Cloud Storage")

@receiver(post_delete, sender=Video)
def delete_gcs_video(sender, instance, **kwargs):
    """Main function to delete video files and related folders in Google Cloud Storage."""
    try:
        logger.info(f"Connecting to Google Cloud Storage with credentials: {settings.GS_CREDENTIALS}")
        client = storage.Client(credentials=settings.GS_CREDENTIALS)
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        
        _, filename = os.path.split(instance.video_file.name)
        base_path = os.path.splitext(filename)[0]

        delete_hls_folder(bucket, base_path)
        delete_video_poster(bucket, base_path)
        delete_text_subfolder(bucket, base_path)
        delete_myfilms_subfolder(bucket, base_path)

    except Exception as e:
        logger.error(f"Error deleting files from Google Cloud Storage: {e}")
