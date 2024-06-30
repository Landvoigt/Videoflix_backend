from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
import redis
from django.views.decorators.http import require_http_methods


redis_client = redis.StrictRedis(host='localhost', port=6379, db=1)

# @require_http_methods(["GET"])
# def get_video_url(request):
#     video_key = request.GET.get('video_key')

#     if not video_key:
#         return JsonResponse({'error': 'Video key is required'}, status=400)

#     cached_video_url = redis_client.get(video_key)
#     if cached_video_url:
#         print('Video URL from cache:', cached_video_url.decode('utf-8'))
#         return JsonResponse({'video_url': cached_video_url.decode('utf-8')})

#     video_url = f'https://storage.googleapis.com/videoflix-videos/hls/{video_key}/master.m3u8'

#     print('Generated video URL:', video_url)

#     redis_client.setex(video_key, 3600, video_url)
    

#     return JsonResponse({'video_url': video_url})

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
