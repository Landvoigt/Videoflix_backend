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



@api_view(["GET"])
def get_poster_and_text(request):
    poster_cache_key = 'poster_urls'
    poster_urls = redis_client.get(poster_cache_key)
    if poster_urls:
        poster_urls = json.loads(poster_urls)
        print('Poster URLs from cache:', poster_urls)
    else:
        try:
            prefix = 'video-posters/'
            blobs = list(gcs_bucket.list_blobs(prefix=prefix))
            poster_urls = [f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{blob.name}' for blob in blobs]
            redis_client.setex(poster_cache_key, 3600, json.dumps(poster_urls))
        except Exception as e:
            return Response({'error': f'Error fetching poster URLs: {str(e)}'}, status=500)

    text_cache_key = 'gcs_video_text_data'
    gcs_data = redis_client.get(text_cache_key)
    if gcs_data:
        gcs_data = json.loads(gcs_data)
        print('GCS data from cache:', gcs_data)
    else:
        try:
            prefix = 'text/'
            blobs = gcs_bucket.list_blobs(prefix=prefix)
            gcs_data = []
            for blob in blobs:
                if blob.name.endswith('/description.txt'):
                    subfolder = blob.name.split('/')[1]
                    title_blob = gcs_bucket.get_blob(f'text/{subfolder}/title.txt')
                    category_blob = gcs_bucket.get_blob(f'text/{subfolder}/category.txt')
                    data = {
                        'subfolder': subfolder,
                        'description': blob.download_as_text(),
                        'title': title_blob.download_as_text() if title_blob else '',
                        'category': category_blob.download_as_text() if category_blob else '',
                    }
                    gcs_data.append(data)
            redis_client.setex(text_cache_key, 3600, json.dumps(gcs_data))
        except Exception as e:
            return Response({'error': f'Error fetching GCS video text data: {str(e)}'}, status=500)
    
    response_data = {
        'poster_urls': poster_urls,
        'gcs_video_text_data': gcs_data
    }
    return Response(response_data)



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
    
    return Response({'subfolders': subfolders})