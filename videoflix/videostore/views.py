from dataclasses import dataclass
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import redis
from django.views.decorators.http import require_http_methods
from google.cloud import storage
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse, HttpResponseBadRequest


redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
gcs_client = storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)
gcs_bucket = gcs_client.bucket(settings.GS_BUCKET_NAME)

@dataclass
class VideoData:
    subfolder: str
    title: str
    description: str
    category: str
    hlsPlaylistUrl: str
    posterUrlGcs: str
    age: str
    resolution: str
    release_date: str
    video_duration: str

@api_view(["GET"])
def get_poster_and_text(request):
    try:
        poster_urls = get_poster_urls()
        gcs_data = get_gcs_video_text_data(poster_urls)
        return Response([video.__dict__ for video in gcs_data])
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
def get_poster_urls():
    poster_cache_key = 'poster_urls'
    poster_urls = redis_client.get(poster_cache_key)
    if poster_urls:
        return json.loads(poster_urls)
    
    try:
        prefix = 'video-posters/'
        blobs = list(gcs_bucket.list_blobs(prefix=prefix))
        poster_urls = [f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{blob.name}' for blob in blobs]
        redis_client.setex(poster_cache_key, 3600, json.dumps(poster_urls))
        return poster_urls
    except Exception as e:
        raise Exception(f'Error fetching poster URLs: {str(e)}')

def get_gcs_video_text_data(poster_urls):
    text_cache_key = 'gcs_video_text_data'
    gcs_data = redis_client.get(text_cache_key)
    if gcs_data:
        return [VideoData(**video) for video in json.loads(gcs_data)]
    
    try:
        gcs_data = fetch_video_text_data_from_gcs(poster_urls)
        cache_gcs_video_text_data(text_cache_key, gcs_data)
        return gcs_data
    except Exception as e:
        raise Exception(f'Error fetching GCS video text data: {str(e)}')


def create_video_data_from_blob(blob, poster_urls):
    subfolder = extract_subfolder_from_blob(blob)

    playlist_url_blob = gcs_bucket.get_blob(f'text/{subfolder}/hlsPlaylist.txt')
    hlsPlaylistUrl = playlist_url_blob.download_as_text() if playlist_url_blob else ''
    
    title_blob = gcs_bucket.get_blob(f'text/{subfolder}/title.txt')
    title = title_blob.download_as_text() if title_blob else ''
    
    category_blob = gcs_bucket.get_blob(f'text/{subfolder}/category.txt')
    category = category_blob.download_as_text() if category_blob else ''
    
    age_blob = gcs_bucket.get_blob(f'text/{subfolder}/age.txt')
    age = age_blob.download_as_text().strip() if age_blob else '0'
    
    resolution_blob = gcs_bucket.get_blob(f'text/{subfolder}/resolution.txt')
    resolution = resolution_blob.download_as_text().strip() if resolution_blob else 'HD'
    
    release_date_blob = gcs_bucket.get_blob(f'text/{subfolder}/release_date.txt')
    release_date = release_date_blob.download_as_text().strip() if release_date_blob else '2020'
    
    video_duration_blob = gcs_bucket.get_blob(f'text/{subfolder}/ video_duration.txt')
    video_duration = release_date_blob.download_as_text().strip() if video_duration_blob else '00:00:00'
    
    poster_url = next((url for url in poster_urls if subfolder in url), None)
    
    return VideoData(
        subfolder=subfolder,
        title=title,
        description=blob.download_as_text(),
        category=category,
        hlsPlaylistUrl=hlsPlaylistUrl,
        age=age,
        resolution=resolution,
        posterUrlGcs=poster_url,
        release_date=release_date,
        video_duration=video_duration
    )


def extract_subfolder_from_blob(blob):
    return blob.name.split('/')[1]


def cache_gcs_video_text_data(text_cache_key, gcs_data):
    redis_client.setex(text_cache_key, 3600, json.dumps([video.__dict__ for video in gcs_data]))


def fetch_video_text_data_from_gcs(poster_urls):
    prefix = 'text/'
    blobs = gcs_bucket.list_blobs(prefix=prefix)
    gcs_data = []
    for blob in blobs:
        if blob.name.endswith('/description.txt'):
            video_data = create_video_data_from_blob(blob, poster_urls)
            gcs_data.append(video_data)
    return gcs_data


@require_http_methods(["GET"])
def get_preview_video(request):
    video_key = request.GET.get('video_key')
    resolution = request.GET.get('resolution') 

    if not video_key or not resolution:
        return JsonResponse({'error': 'Video key and resolution are required'}, status=400)

    cache_key = f"{video_key}_{resolution}"
    try:
        cached_video_url = redis_client.get(cache_key)
        if cached_video_url:
            video_url = cached_video_url.decode('utf-8')
            print('Video URL from cache:', video_url)
            return JsonResponse({'video_url': video_url})
        
        video_url = f'https://storage.googleapis.com/videoflix-storage/hls/{video_key}/{resolution}.m3u8'
        print('Generated video URL:', video_url)
        redis_client.setex(cache_key, 3600, video_url)

        return JsonResponse({'video_url': video_url})
    except redis.RedisError as e:
        print(f'Redis error: {str(e)}')
        return JsonResponse({'error': 'Internal server error while accessing cache'}, status=500)
    except Exception as e:
        print(f'Error: {str(e)}')
        return JsonResponse({'error': 'Internal server error'}, status=500)



@require_http_methods(["GET"])
def get_full_video(request):
    video_key = request.GET.get('video_key')
    resolution = request.GET.get('resolution')

    if not video_key or not resolution:
        return HttpResponseBadRequest({'error': 'Video key and resolution are required'})

    cache_key = f"{video_key}_{resolution}"
    cached_video_url = redis_client.get(cache_key)
    if cached_video_url:
        print('Video URL from cache:', cached_video_url.decode('utf-8'))
        return JsonResponse({'video_url': cached_video_url.decode('utf-8')})

    video_url = f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/hls/{video_key}/{resolution}.m3u8'

    print('Generated video URL:', video_url)
    redis_client.setex(cache_key, 3600, video_url)

    return JsonResponse({'video_url': video_url})



@csrf_exempt
@require_http_methods(["POST"])
def create_gcs_myFilms(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        file_name = data.get('file_name')
        
        if not file_name:
            return JsonResponse({'error': 'file_name is required'}, status=400)
        
        main_folder = 'myFilms/'
        sub_folder = f'{main_folder}{file_name}/'

        if not gcs_bucket.blob(sub_folder).exists():
            gcs_bucket.blob(sub_folder + 'placeholder.txt').upload_from_string('')
            print(f'Unterordner "{sub_folder}" erstellt')

        folder_url = f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{sub_folder}'

        return JsonResponse({'message': f'Ordner "{sub_folder}" erfolgreich erstellt', 'url': folder_url}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(["GET"])
def get_myFilms(request):
    cache_key = 'my_films_subfolders'
    subfolders = redis_client.get(cache_key)
    
    if subfolders:
        subfolders = json.loads(subfolders)
        print('Subfolders from cache:', subfolders)
    else:
        try:
            prefix = 'myFilms/'
            blobs = gcs_bucket.list_blobs(prefix=prefix)
            subfolder_names = set()
            
            for blob in blobs:
                if blob.name.endswith('placeholder.txt'):
                    parts = blob.name.split('/')
                    if len(parts) > 1:
                        subfolder_name = parts[1]
                        subfolder_names.add(subfolder_name)
            
            subfolders = list(subfolder_names)
            redis_client.setex(cache_key, 3600, json.dumps(subfolders))
        except Exception as e:
            return Response({'error': f'Error fetching subfolder names: {str(e)}'}, status=500)
    
    return Response(subfolders)