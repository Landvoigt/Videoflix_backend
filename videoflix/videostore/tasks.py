import os
import subprocess
import glob
import logging
from django.conf import settings
from google.cloud import storage
from videostore.models import Video
import time


os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
logger = logging.getLogger(__name__)


def upload_to_gcs(local_file_name, gcs_file_path):
    try:
        client = storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(gcs_file_path)       
        blob.upload_from_filename(local_file_name)           
        logger.info(f"Uploaded {local_file_name} to {gcs_file_path}")
    except Exception as e:
        error_msg = f"Error uploading {local_file_name} to GCS: {e}"
        logger.error(error_msg)


def create_master_playlist(base_path, resolutions):
    master_playlist_path = os.path.join(base_path, 'master.m3u8')
    with open(master_playlist_path, 'w') as master_playlist:
        master_playlist.write("#EXTM3U\n")
        master_playlist.write("#EXT-X-VERSION:3\n\n")

        for resolution in resolutions:
            if resolution == '360':
                bandwidth = 800000
                width = 640
                height = 360
            elif resolution == '480':
                bandwidth = 1400000
                width = 854
                height = 480
            elif resolution == '720':
                bandwidth = 2800000
                width = 1280
                height = 720
            elif resolution == '1080':
                bandwidth = 5000000
                width = 1920
                height = 1080

            playlist_filename = f"{resolution}p.m3u8"
            master_playlist.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={width}x{height}\n")
            master_playlist.write(f"{playlist_filename}\n\n")

    return master_playlist_path


def check_video_file(video_name):
    video_path = os.path.join(settings.MEDIA_ROOT, 'videos', f'{video_name}.mp4')
    
    if os.path.isfile(video_path):
        print(f"Die Datei existiert: {video_path}")
    else:
        print(f"Die Datei existiert nicht: {video_path}")



def convert_to_hls(video_id, video_name=None):
    print(f"Starting conversion for video id {video_id}")

    time.sleep(3) 
    check_video_file(video_name)
    
    base_path = os.path.join(settings.MEDIA_ROOT, 'videos', video_name)

    try:
        video = Video.objects.get(id=video_id)
        print(f"Found video in database: {video.title}")
    except Video.DoesNotExist:
        print(f"Video with id {video_id} does not exist.")
        return

    source = f'{base_path}.mp4'  
    if video_name is None:
        video_name = str(video_id)
    
    output_directory = base_path 
    os.makedirs(output_directory, exist_ok=True)

    print(f"Extracting poster for video {video_name}...")
    poster_url = extract_and_upload_poster(source, video_name)
    if poster_url:
        print(f"Poster extracted and uploaded to {poster_url}")
    else:
        print("Failed to extract and upload poster")

    cmd_base = [
        'ffmpeg',
        '-i', source,
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

    resolutions = ['360', '480', '720', '1080']
    bitrates = {'360': '800k', '480': '1400k', '720': '2800k', '1080': '5000k'}

    for resolution in resolutions:
        print(f"Starting conversion to {resolution}p...")
        scale = f'scale=-2:{resolution}'
        bitrate = bitrates[resolution]
        output_ts = f'{output_directory}/{resolution}p_%03d.ts'
        output_m3u8 = f'{output_directory}/{resolution}p.m3u8'
        cmd = cmd_base + ['-vf', scale, '-b:v', bitrate, '-hls_segment_filename', output_ts, output_m3u8]

        print(f"Running FFmpeg command for {resolution}p: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error converting video id {video_id} for resolution {resolution}: {result.stderr}")
            return

    print("Creating master playlist...")
    master_playlist_path = create_master_playlist(output_directory, resolutions)

    if os.path.exists(master_playlist_path):
        gcs_master_path = f"hls/{video_name}/master.m3u8"
        print(f"Uploading master playlist to GCS: {gcs_master_path}")
        upload_to_gcs(master_playlist_path, gcs_master_path)
    else:
        print(f"Master playlist {master_playlist_path} does not exist. Skipping upload.")

    for resolution in resolutions:
        local_playlist = f"{output_directory}/{resolution}p.m3u8"
        if os.path.exists(local_playlist):
            gcs_playlist_path = f"hls/{video_name}/{resolution}p.m3u8"
            print(f"Uploading {resolution}p playlist to GCS: {gcs_playlist_path}")
            upload_to_gcs(local_playlist, gcs_playlist_path)

            ts_files = glob.glob(f"{output_directory}/{resolution}p_*.ts")
            for ts_file in ts_files:
                if os.path.exists(ts_file):
                    gcs_ts_path = f"hls/{video_name}/{os.path.basename(ts_file)}"
                    print(f"Uploading TS file to GCS: {gcs_ts_path}")
                    upload_to_gcs(ts_file, gcs_ts_path)
                else:
                    print(f"TS file {ts_file} does not exist for resolution {resolution} and video id {video_id}")
        else:
            print(f"Resolution {resolution} playlist {local_playlist} does not exist for video id {video_id}")

    print(f"Finished convert_to_hls function for video id {video_id}")



def extract_and_upload_poster(video_path, video_name):
    try:
        base_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'videos'))
        posters_dir = os.path.join(base_path, 'posters')
        os.makedirs(posters_dir, exist_ok=True)
        local_file_name = os.path.abspath(os.path.join(posters_dir, f'{video_name}.jpg'))

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', '00:00:10.000',
            '-vframes', '1',
            '-update', '1', 
            local_file_name 
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Error extracting poster for video {video_name}: {result.stderr}"
            logger.error(error_msg)
            return None
        gcs_poster_path = f'video-posters/{video_name}.jpg'
        upload_to_gcs(local_file_name, gcs_poster_path)        
        return gcs_poster_path
    except Exception as e:
        error_msg = f"Error extracting and uploading poster for video {video_name}: {e}"
        logger.error(error_msg)
        return None
