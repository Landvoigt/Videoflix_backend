from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.db.models.signals import post_save
from django_rq import get_queue
from videostore.models import Video
from videostore.signals import video_post_save, enqueue_video_task
from unittest import mock
import pytest
from videostore.signals import delete_hls_folder, delete_video_poster, delete_text_subfolder, delete_myfilms_subfolder, delete_gcs_video

class VideoSignalTests(TestCase):
    @patch('videostore.signals.enqueue_video_task') 
    def test_video_post_save_signal_created(self, mock_enqueue_task):
        video_instance = Video.objects.create(
            title="Test Video", 
            video_file="test_video.mp4"
        )

        video_post_save(Video, instance=video_instance, created=True)

        mock_enqueue_task.assert_called_once_with(video_instance)

    @patch('videostore.signals.enqueue_video_task')  
    def test_video_post_save_signal_not_created(self, mock_enqueue_task):
        video_instance = Video.objects.create(
            title="Test Video", 
            video_file="test_video.mp4"
        )

        video_post_save(Video, instance=video_instance, created=False)

        mock_enqueue_task.assert_not_called()

    @patch('videostore.signals.logger')  
    @patch('videostore.signals.get_queue')  
    def test_enqueue_video_task_no_video_file(self, mock_get_queue, mock_logger):
        video_instance = MagicMock(video_file=None)

        enqueue_video_task(video_instance)

        mock_logger.error.assert_called_once_with(f"No video file associated with instance {video_instance.id}")

        mock_get_queue.assert_not_called()

    @patch('videostore.signals.os.path.splitext')  
    @patch('videostore.signals.get_video_duration')  
    @patch('videostore.signals.get_queue')  
    @patch('videostore.signals.convert_to_hls')  
    def test_enqueue_video_task_success(self, mock_convert_to_hls, mock_get_queue, mock_get_video_duration, mock_splitext):
        video_instance = MagicMock()
        video_instance.video_file.path = "/media/videos/test_video.mp4"

        mock_queue = MagicMock()
        mock_get_queue.return_value = mock_queue

        mock_splitext.return_value = ("test_video", ".mp4")

        enqueue_video_task(video_instance)

        mock_get_video_duration.assert_called_once_with(video_instance)

        mock_queue.enqueue.assert_called_once_with(mock_convert_to_hls, video_instance.id, video_name="test_video")
        
        
    @pytest.fixture
    def mock_bucket():
        return mock.Mock()

    @pytest.fixture
    def mock_blob():
        return mock.Mock()

    @pytest.fixture
    def mock_list_blobs(mock_bucket, mock_blob):
        mock_bucket.list_blobs.return_value = [mock_blob]
        return mock_bucket.list_blobs

    def test_delete_hls_folder(mock_bucket, mock_list_blobs, mock_blob, caplog):
        base_path = "test-video"
        delete_hls_folder(mock_bucket, base_path)
        mock_bucket.list_blobs.assert_called_once_with(prefix="hls/test-video/")
        mock_blob.delete.assert_called_once()
        assert f"Deleted {mock_blob.name} from Google Cloud Storage" in caplog.text
        assert "Deleted all files in folder hls/test-video/ from Google Cloud Storage" in caplog.text


    def test_delete_video_poster(mock_bucket, mock_blob, caplog):
        base_path = "test-video"
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        delete_video_poster(mock_bucket, base_path)
        mock_bucket.blob.assert_called_once_with("video-posters/test-video.jpg")
        mock_blob.delete.assert_called_once()
        assert "Deleted poster video-posters/test-video.jpg from Google Cloud Storage" in caplog.text


    def test_delete_video_poster_not_found(mock_bucket, mock_blob, caplog):
        base_path = "test-video"
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob
        delete_video_poster(mock_bucket, base_path)
        mock_bucket.blob.assert_called_once_with("video-posters/test-video.jpg")
        mock_blob.delete.assert_not_called()
        assert "Poster video-posters/test-video.jpg not found in Google Cloud Storage" in caplog.text


    def test_delete_text_subfolder(mock_bucket, mock_list_blobs, mock_blob, caplog):
        base_path = "test-video"
        delete_text_subfolder(mock_bucket, base_path)
        mock_bucket.list_blobs.assert_called_once_with(prefix="text/test-video/")
        mock_blob.delete.assert_called_once()
        assert f"Deleted {mock_blob.name} from Google Cloud Storage" in caplog.text
        assert "Deleted all files in subfolder text/test-video/ from Google Cloud Storage" in caplog.text


    def test_delete_myfilms_subfolder(mock_bucket, mock_list_blobs, mock_blob, caplog):
        base_path = "test-video"
        delete_myfilms_subfolder(mock_bucket, base_path)
        mock_bucket.list_blobs.assert_called_once_with(prefix="myFilms/test-video/")
        mock_blob.delete.assert_called_once()
        assert f"Deleted {mock_blob.name} from Google Cloud Storage" in caplog.text
        assert "Deleted all files in subfolder myFilms/test-video/ from Google Cloud Storage" in caplog.text


    def test_delete_gcs_video_signal(mocker, mock_bucket, caplog):
        mocker.patch("videostore.signals.storage.Client", return_value=mock.Mock())
        mocker.patch("videostore.signals.delete_hls_folder")
        mocker.patch("videostore.signals.delete_video_poster")
        mocker.patch("videostore.signals.delete_text_subfolder")
        mocker.patch("videostore.signals.delete_myfilms_subfolder")

        video_instance = mock.Mock(video_file=mock.Mock(name="test-video.mp4"))
        delete_gcs_video(sender=Video, instance=video_instance)

        assert "Connecting to Google Cloud Storage" in caplog.text
