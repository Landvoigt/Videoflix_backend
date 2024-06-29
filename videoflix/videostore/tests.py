import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from django_rq import get_queue
from .models import Video
from .tasks import convert_to_hls
from unittest import mock
from .signals import delete_django_admin_video
from unittest.mock import patch
from .signals import delete_gcs_video
from django.conf import settings
from .tasks import upload_to_gcs 
import unittest
import tempfile
from .tasks import create_master_playlist
from unittest.mock import patch, MagicMock



class VideoPostSaveSignalTests(TestCase):

    def setUp(self):
        video_content = b'some_video_content'
        video_file = SimpleUploadedFile('video.mp4', video_content)
        self.instance = Video.objects.create(title='Test Video', description='Description of the video', video_file=video_file)

    def test_video_post_save_signal(self):
        queue = get_queue('default', autocommit=True) 
        post_save.send(sender=Video, instance=self.instance, created=True)
        job = queue.jobs[-1] 
        self.assertEqual(job.func, convert_to_hls) 
        self.assertEqual(job.args[0], self.instance.id)  


class ConvertToHLSTestCase(TestCase):
    def setUp(self):
        self.video_id = 1
        self.video_name = 'test_video'
        self.video_path = '/media/videos/test_video.mp4' 
        self.video = Video.objects.create(id=self.video_id, video_file=self.video_path)
        self.base_media_path = os.path.join(settings.MEDIA_ROOT, 'videos')

    @mock.patch('videostore.tasks.upload_to_gcs')
    @mock.patch('subprocess.run')
    def test_convert_to_hls_success(self, mock_subprocess_run, mock_upload_to_gcs):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stderr = ''
        convert_to_hls(self.video_id, self.video_name)
        mock_subprocess_run.assert_called_once()
        mock_upload_to_gcs.assert_called()  

    @mock.patch('videostore.tasks.upload_to_gcs')
    @mock.patch('subprocess.run')
    def test_convert_to_hls_video_not_found(self, mock_subprocess_run, mock_upload_to_gcs):
        Video.objects.filter(id=self.video_id).delete()
        convert_to_hls(self.video_id, self.video_name)
        mock_subprocess_run.assert_not_called()
        mock_upload_to_gcs.assert_not_called()

    @mock.patch('videostore.tasks.upload_to_gcs')
    @mock.patch('subprocess.run')
    def test_convert_to_hls_conversion_failure(self, mock_subprocess_run, mock_upload_to_gcs):
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = 'ffmpeg error'
        convert_to_hls(self.video_id, self.video_name)
        mock_upload_to_gcs.assert_not_called()

if __name__ == '__main__':
    unittest.main()


class CreateMasterPlaylistTestCase(TestCase):

    def test_create_master_playlist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            resolutions = ['360', '480', '720', '1080'] 
            master_playlist_path = create_master_playlist(temp_dir, resolutions)
            self.assertTrue(os.path.exists(master_playlist_path))
            with open(master_playlist_path, 'r') as master_playlist:
                content = master_playlist.read()
                expected_content = (
                    "#EXTM3U\n"
                    "#EXT-X-VERSION:3\n\n"
                    "#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360\n360p.m3u8\n\n"
                    "#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480\n480p.m3u8\n\n"
                    "#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720\n720p.m3u8\n\n"
                    "#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080\n1080p.m3u8\n\n"
                )
                
                self.assertEqual(content, expected_content)
                               
                               
class UploadToGCSTestCase(TestCase):

    @patch('videostore.tasks.storage.Client')
    @patch('videostore.tasks.logger')
    def test_upload_to_gcs(self, mock_logger, MockStorageClient):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test content')
            local_file_path = temp_file.name
        gcs_file_path = 'test_bucket/test_file'
        mock_client_instance = MockStorageClient.return_value
        mock_bucket = mock_client_instance.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        upload_to_gcs(local_file_path, gcs_file_path)
        mock_blob.upload_from_filename.assert_called_once_with(local_file_path)
        mock_logger.info.assert_called_with(f"Uploaded {local_file_path} to {gcs_file_path}")
        os.remove(local_file_path)

    @patch('videostore.tasks.storage.Client')
    @patch('videostore.tasks.logger')
    def test_upload_to_gcs_file_not_found(self, mock_logger, MockStorageClient):
        local_file_path = 'non_existent_file.txt'
        gcs_file_path = 'test_bucket/test_file'
        upload_to_gcs(local_file_path, gcs_file_path)
        mock_logger.warning.assert_called_with(f"File not found: {local_file_path}. Skipping upload to GCS.")
    @patch('videostore.tasks.storage.Client')
    @patch('videostore.tasks.logger')
    def test_upload_to_gcs_exception(self, mock_logger, MockStorageClient):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test content')
            local_file_path = temp_file.name
        gcs_file_path = 'test_bucket/test_file'
        mock_client_instance = MockStorageClient.return_value
        mock_bucket = mock_client_instance.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        mock_blob.upload_from_filename.side_effect = Exception('Test exception')
        upload_to_gcs(local_file_path, gcs_file_path)
        mock_logger.error.assert_called_with(f"Error uploading {local_file_path} to GCS: Test exception")
        os.remove(local_file_path)


class VideoDeleteTestCase(TestCase):

    def setUp(self):
        self.video = Video.objects.create(
            title='Test Video',
            video_file=SimpleUploadedFile('test_video.mp4', b'content')
        )

    def test_video_deletion(self):
        try:
            self.video.delete()
        except Exception as e:
            self.fail(f"Deleting video raised an exception: {e}")

        video_path = self.video.video_file.path
        self.assertFalse(os.path.isfile(video_path), f"Video file {video_path} was not deleted.")

    def tearDown(self):
        video_path = self.video.video_file.path
        if os.path.isfile(video_path):
            os.remove(video_path)


class GCSDeleteTestCase(TestCase):

    @patch('google.cloud.storage.Client')
    def test_delete_gcs_video(self, MockClient):
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        video = Video.objects.create(
            title='Test Video',
            video_file=SimpleUploadedFile('test_video.mp4', b'content')
        )

        delete_gcs_video(sender=Video, instance=video)
        mock_client_instance.bucket.assert_called_once_with(settings.GS_BUCKET_NAME)
        
        
        
        
        
        
        
        
        
        
        
# from django.test import TestCase, Client
# from unittest.mock import patch, MagicMock
# from django.conf import settings
# from google.cloud import storage
# import json

# class VideoUrlTestCase(TestCase):

#     @patch('google.cloud.storage.Client')
#     @patch('redis.StrictRedis')
#     def test_get_video_url(self, MockRedis, MockStorageClient):
#         # Mock Redis client
#         mock_redis_instance = MockRedis.return_value
#         mock_redis_instance.get.return_value = None  # Simulate Redis cache miss
#         mock_redis_instance.setex.return_value = True  # Simulate successful cache set

#         # Mock Storage client
#         mock_blob = MagicMock()
#         mock_blob.public_url = 'http://example.com/video.mp4'
#         mock_bucket = MagicMock()
#         mock_bucket.blob.return_value = mock_blob
#         mock_storage_client_instance = MockStorageClient.from_service_account_json.return_value
#         mock_storage_client_instance.bucket.return_value = mock_bucket

#         # Setup test client
#         client = Client()

#         # Mock request with video_key parameter
#         video_key = '12345'
#         response = client.get(f'/get-video-url/?video_key={video_key}')

#         # Assert HTTP response status code
#         self.assertEqual(response.status_code, 200)

#         # Assert response JSON content
#         content = json.loads(response.content)
#         self.assertIn('video_url', content)
#         self.assertEqual(content['video_url'], 'http://example.com/video.mp4')

#         # Assert Redis client methods called
#         mock_redis_instance.get.assert_called_once_with(video_key)
#         mock_redis_instance.setex.assert_called_once_with(video_key, 3600, 'http://example.com/video.mp4')

#         # Assert Storage client methods called
#         mock_storage_client_instance.bucket.assert_called_once_with(settings.GS_BUCKET_NAME)
#         mock_bucket.blob.assert_called_once_with(f'hls/{video_key}/master.m3u8')
    
# def test_get_video_url_missing_video_key(self):
#     # Setup test client
#     client = Client()

#     # Mock request without video_key parameter
#     response = client.get('/get-video-url/')

#     # Assert HTTP response status code
#     self.assertEqual(response.status_code, 400)

#     # Assert error message in response JSON content
#     content = json.loads(response.content)
#     self.assertIn('error', content)
#     self.assertEqual(content['error'], 'Video key is required')    
# @patch('google.cloud.storage.Client')
# @patch('redis.StrictRedis')


# def test_get_video_url_redis_exception(self, MockRedis, MockStorageClient):
#     # Mock Redis client exception
#     mock_redis_instance = MockRedis.return_value
#     mock_redis_instance.get.side_effect = Exception('Mock Redis error')

#     # Setup test client
#     client = Client()

#     # Mock request with video_key parameter
#     video_key = '12345'
#     response = client.get(f'/get-video-url/?video_key={video_key}')

#     # Assert HTTP response status code
#     self.assertEqual(response.status_code, 500)

#     # Assert error message in response JSON content
#     content = json.loads(response.content)
#     self.assertIn('error', content)
#     self.assertEqual(content['error'], 'Mock Redis error')

# @patch('google.cloud.storage.Client')
# @patch('redis.StrictRedis')
# def test_get_video_url_storage_exception(self, MockRedis, MockStorageClient):
#     # Mock Redis client
#     mock_redis_instance = MockRedis.return_value
#     mock_redis_instance.get.return_value = None  # Simulate Redis cache miss
#     mock_redis_instance.setex.return_value = True  # Simulate successful cache set

#     # Mock Storage client exception
#     mock_storage_client_instance = MockStorageClient.from_service_account_json.return_value
#     mock_bucket = MagicMock()
#     mock_storage_client_instance.bucket.return_value = mock_bucket
#     mock_bucket.blob.side_effect = Exception('Mock storage error')

#     # Setup test client
#     client = Client()

#     # Mock request with video_key parameter
#     video_key = '12345'
#     response = client.get(f'/get-video-url/?video_key={video_key}')

#     # Assert HTTP response status code
#     self.assertEqual(response.status_code, 500)

#     # Assert error message in response JSON content
#     content = json.loads(response.content)
#     self.assertIn('error', content)
#     self.assertEqual(content['error'], 'Mock storage error')
