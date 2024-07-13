from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
import redis
from django.views.decorators.http import require_http_methods
from google.cloud import storage
from .models import Video
from django.views.decorators.csrf import csrf_exempt
import json


redis_client = redis.StrictRedis(host='localhost', port=6379, db=1)



@require_http_methods(["GET"])
def get_video_url(request):
    video_key = request.GET.get('video_key')
    resolution = request.GET.get('resolution') 

    if not video_key or not resolution:
        return JsonResponse({'error': 'Video key and resolution are required'}, status=400)

    cache_key = f"{video_key}_{resolution}"
    cached_video_url = redis_client.get(cache_key)
    if cached_video_url:
        print('Video URL from cache:', cached_video_url.decode('utf-8'))
        return JsonResponse({'video_url': cached_video_url.decode('utf-8')})

    video_url = f'https://storage.googleapis.com/videoflix-videos/hls/{video_key}/{resolution}.m3u8'

    print('Generated video URL:', video_url)
    redis_client.setex(cache_key, 3600, video_url)

    return JsonResponse({'video_url': video_url})



@require_http_methods(["GET"])
def get_poster_urls(request):
    try:
        client = storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        prefix = 'video-posters/'
        blobs = list(bucket.list_blobs(prefix=prefix))
        poster_urls = [f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{blob.name}' for blob in blobs]

        return JsonResponse({'poster_urls': poster_urls})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    

@require_http_methods(["GET"])
def get_all_video_urls(request):
    try:
        client = storage.Client(credentials=settings.GS_CREDENTIALS, project=settings.GS_PROJECT_ID)
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        prefix = 'hls/'
        blobs = bucket.list_blobs(prefix=prefix)
        video_urls = [f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{blob.name}' 
                      for blob in blobs if blob.name.endswith('360p.m3u8')]

        return JsonResponse({'video_urls': video_urls})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
 
 

def get_all_videos(request):
    try:
        videos = Video.objects.all()
        video_list = []
        for video in videos:
            video_data = {
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'video_url': video.video_file.url if video.video_file else '',
                'hls_playlist': video.hls_playlist if video.hls_playlist else ''
            }
            video_list.append(video_data)

        return JsonResponse({'videos': video_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def check_video_data(request):
    if request.method == 'POST':
        video_urls = json.loads(request.body).get('video_urls', [])
        # Extrahiere die Dateinamen aus den URLs und überprüfe, ob sie in der Datenbank vorhanden sind
        video_keys = [url.split('/')[-2] for url in video_urls]
        is_available = all(Video.objects.filter(video_file__contains=video_key).exists() for video_key in video_keys)
        return JsonResponse({'is_available': is_available})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


    
    
