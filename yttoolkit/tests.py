from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json

from .models import YouTubeMP3
from .tasks import download_youtube_mp3


class YouTubeMP3ModelTest(TestCase):
    """Test the YouTubeMP3 model"""

    def setUp(self):
        self.test_url = "https://www.youtube.com/watch?v=test123"

    def test_create_youtube_mp3(self):
        """Test creating a YouTubeMP3 instance"""
        youtube_mp3 = YouTubeMP3.objects.create(video_url=self.test_url)

        self.assertEqual(youtube_mp3.video_url, self.test_url)
        self.assertEqual(youtube_mp3.download_status, 'pending')
        self.assertIsNone(youtube_mp3.video_title)
        self.assertIsNone(youtube_mp3.file_size)

    def test_invalid_url_validation(self):
        """Test URL validation"""
        with self.assertRaises(ValueError):
            youtube_mp3 = YouTubeMP3(video_url="invalid-url")
            youtube_mp3.save()

    def test_file_size_mb_property(self):
        """Test file_size_mb property"""
        youtube_mp3 = YouTubeMP3.objects.create(
            video_url=self.test_url,
            file_size=1048576  # 1 MB in bytes
        )

        self.assertEqual(youtube_mp3.file_size_mb, 1.0)

    def test_str_representation(self):
        """Test string representation"""
        youtube_mp3 = YouTubeMP3.objects.create(video_url=self.test_url)
        expected = f"{self.test_url} - pending"
        self.assertEqual(str(youtube_mp3), expected)


class YouTubeMP3ViewTest(TestCase):
    """Test the views"""

    def setUp(self):
        self.test_url = "https://www.youtube.com/watch?v=test123"

    def test_download_list_view(self):
        """Test the download list view"""
        # Create some test data
        YouTubeMP3.objects.create(video_url=self.test_url)

        response = self.client.get(reverse('yttoolkit:download_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_url)

    @patch('yttoolkit.models.YouTubeMP3.start_download')
    def test_start_download_view(self, mock_start_download):
        """Test starting a download via POST"""
        mock_task = MagicMock()
        mock_task.id = 'test-task-id'
        mock_start_download.return_value = mock_task

        response = self.client.post(
            reverse('yttoolkit:start_download'),
            {'video_url': self.test_url}
        )

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(YouTubeMP3.objects.filter(video_url=self.test_url).exists())

    def test_api_start_download(self):
        """Test the API endpoint for starting downloads"""
        with patch('yttoolkit.models.YouTubeMP3.start_download') as mock_start_download:
            mock_task = MagicMock()
            mock_task.id = 'test-task-id'
            mock_start_download.return_value = mock_task

            response = self.client.post(
                reverse('yttoolkit:api_start_download'),
                json.dumps({'video_url': self.test_url}),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['task_id'], 'test-task-id')

    def test_api_download_status(self):
        """Test the API endpoint for checking download status"""
        youtube_mp3 = YouTubeMP3.objects.create(
            video_url=self.test_url,
            video_title="Test Video",
            download_status='completed',
            file_size=1048576
        )

        response = self.client.get(
            reverse('yttoolkit:api_download_status', args=[youtube_mp3.id])
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['video_url'], self.test_url)
        self.assertEqual(data['download_status'], 'completed')
        self.assertEqual(data['file_size_mb'], 1.0)


class YouTubeMP3TaskTest(TestCase):
    """Test the Celery tasks"""

    def setUp(self):
        self.test_url = "https://www.youtube.com/watch?v=test123"
        self.youtube_mp3 = YouTubeMP3.objects.create(video_url=self.test_url)

    @patch('yttoolkit.tasks.yt_dlp.YoutubeDL')
    def test_download_task_success(self, mock_ydl_class):
        """Test successful download task"""
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock extract_info to return video info
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video Title'
        }

        # Mock file system
        with patch('yttoolkit.tasks.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.name = 'test_video.mp3'
            mock_file.stat.return_value.st_size = 1048576
            mock_path.return_value.glob.return_value = [mock_file]

            # Call the task
            result = download_youtube_mp3(self.youtube_mp3.id)

            # Verify results
            self.assertEqual(result['status'], 'success')

            # Refresh from database
            self.youtube_mp3.refresh_from_db()
            self.assertEqual(self.youtube_mp3.download_status, 'completed')
            self.assertEqual(self.youtube_mp3.video_title, 'Test Video Title')
            self.assertEqual(self.youtube_mp3.file_size, 1048576)

    def test_download_task_not_found(self):
        """Test task with non-existent YouTube MP3 record"""
        result = download_youtube_mp3(99999)  # Non-existent ID

        self.assertEqual(result['status'], 'error')
        self.assertIn('not found', result['message'])

    @patch('yttoolkit.tasks.yt_dlp.YoutubeDL')
    def test_download_task_failure(self, mock_ydl_class):
        """Test task failure handling"""
        # Mock yt-dlp to raise an exception
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Download failed")

        # Call the task
        result = download_youtube_mp3(self.youtube_mp3.id)

        # Verify error handling
        self.assertEqual(result['status'], 'error')

        # Refresh from database
        self.youtube_mp3.refresh_from_db()
        self.assertEqual(self.youtube_mp3.download_status, 'failed')
