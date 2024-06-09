
import subprocess
import os
import time
from .models import Video
import logging

logger = logging.getLogger(__name__)

def convert_to_hls(video_id):
    logger.info(f"Starting conversion for video id {video_id}")
    
    time.sleep(1)  # Verzögerung, sonst findet django video ID nicht!!!!!
    
    try:
        video = Video.objects.get(id=video_id)
        logger.info(f"Found video with id {video_id}")
    except Video.DoesNotExist:
        logger.error(f"Video with id {video_id} does not exist.")
        return
    
    source = video.video_file.path
    base_path = os.path.splitext(source)[0]
    resolutions = ['360', '480', '720', '1080']
    
    hls_playlist_path = f"{base_path}.m3u8"
    
    cmd = [
        'ffmpeg',
        '-i', source,
        '-vf', "scale=w=trunc(iw/2)*2:h=trunc(ih/2)*2",
        '-c:a', 'aac',
        '-ar', '48000',
        '-b:a', '128k',
        '-c:v', 'h264',
        '-profile:v', 'main',
        '-crf', '20',
        '-sc_threshold', '0',
        '-g', '48',
        '-keyint_min', '48',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod'
    ]
    
    for resolution in resolutions:
        cmd.extend([
            '-vf', f'scale=-2:{resolution}',
            '-b:v', f'{int(resolution) * 1000}k',
            '-hls_segment_filename', f'{base_path}_{resolution}p_%03d.ts',
            f'{base_path}_{resolution}p.m3u8'
        ])
    
    cmd.extend([
        '-master_pl_name', hls_playlist_path
    ])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Error converting video id {video_id}: {result.stderr}")
    else:
        logger.info(f"Successfully created HLS playlist at {hls_playlist_path} for video id {video_id}")
        video.hls_playlist = hls_playlist_path
        video.save()



