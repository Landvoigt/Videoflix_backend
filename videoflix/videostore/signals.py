
import glob
import os
import logging
from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import django_rq

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created:
        queue = django_rq.get_queue('default', autocommit=True)
        logger.info(f"Enqueuing video id {instance.id} for conversion")
        from .tasks import convert_to_hls
        queue.enqueue(convert_to_hls, instance.id)

@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.video_file and os.path.isfile(instance.video_file.path):
        os.remove(instance.video_file.path)
        logger.info(f"Deleted video file: {instance.video_file.path}")
    
    base_path = os.path.splitext(instance.video_file.path)[0]
    resolutions = ['360', '480', '720', '1080']
    
    for resolution in resolutions:
        hls_segment_files_pattern = f"{base_path}_{resolution}p_*.ts"
        for hls_segment_file in glob.glob(hls_segment_files_pattern):
            if os.path.isfile(hls_segment_file):
                os.remove(hls_segment_file)
                logger.info(f"Deleted HLS segment file: {hls_segment_file}")
        
        hls_playlist_file = f"{base_path}_{resolution}p.m3u8"
        if os.path.isfile(hls_playlist_file):
            os.remove(hls_playlist_file)
            logger.info(f"Deleted HLS playlist file: {hls_playlist_file}")

    if instance.hls_playlist and os.path.isfile(instance.hls_playlist):
        os.remove(instance.hls_playlist)
        logger.info(f"Deleted HLS master playlist: {instance.hls_playlist}")
