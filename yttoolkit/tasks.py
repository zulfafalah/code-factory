import os
import tempfile
from pathlib import Path

import yt_dlp
from celery import shared_task
from django.conf import settings

from .models import YouTubeMP3


@shared_task(bind=True)
def download_youtube_mp3(self, youtube_mp3_id):
    """
    Celery task to download YouTube video as MP3.

    Args:
        youtube_mp3_id: ID of the YouTubeMP3 model instance
    """
    try:
        # Get the YouTubeMP3 instance
        youtube_mp3 = YouTubeMP3.objects.get(id=youtube_mp3_id)
        youtube_mp3.download_status = 'in_progress'
        youtube_mp3.save()

        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'writesubtitles': False,
                'writeautomaticsub': False,
                'ignoreerrors': False,
            }

            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get video details
                info = ydl.extract_info(youtube_mp3.video_url, download=False)
                video_title = info.get('title', 'Unknown')

                # Update the model with video info
                youtube_mp3.video_title = video_title
                youtube_mp3.save()

                # Now download the video
                ydl.download([youtube_mp3.video_url])

                # Find the downloaded MP3 file
                mp3_files = list(Path(temp_dir).glob('*.mp3'))
                if mp3_files:
                    mp3_file = mp3_files[0]
                    file_size = mp3_file.stat().st_size

                    # Update model with file info
                    youtube_mp3.file_size = file_size
                    youtube_mp3.file_name = mp3_file.name

                    # Here you can add logic to save the file to your preferred storage
                    # For example, upload to S3, save to media folder, etc.
                    # For now, we'll just store the file information

        # Mark as completed
        youtube_mp3.download_status = 'completed'
        youtube_mp3.save()

        return {
            'status': 'success',
            'message': f'Successfully downloaded: {video_title}',
            'file_size': youtube_mp3.file_size,
            'file_name': youtube_mp3.file_name
        }

    except YouTubeMP3.DoesNotExist:
        return {
            'status': 'error',
            'message': f'YouTubeMP3 with id {youtube_mp3_id} not found'
        }

    except yt_dlp.DownloadError as e:
        # Handle download errors
        try:
            youtube_mp3 = YouTubeMP3.objects.get(id=youtube_mp3_id)
            youtube_mp3.download_status = 'failed'
            youtube_mp3.error_message = str(e)
            youtube_mp3.save()
        except YouTubeMP3.DoesNotExist:
            pass

        return {
            'status': 'error',
            'message': f'Download failed: {str(e)}'
        }

    except Exception as e:
        # Handle any other errors
        try:
            youtube_mp3 = YouTubeMP3.objects.get(id=youtube_mp3_id)
            youtube_mp3.download_status = 'failed'
            youtube_mp3.error_message = str(e)
            youtube_mp3.save()
        except YouTubeMP3.DoesNotExist:
            pass

        # Retry the task up to 3 times with exponential backoff
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=e)

        return {
            'status': 'error',
            'message': f'Task failed after retries: {str(e)}'
        }


@shared_task
def cleanup_old_downloads():
    """
    Periodic task to cleanup old completed/failed downloads.
    This can be run periodically to manage storage.
    """
    from datetime import timedelta
    from django.utils import timezone

    # Delete records older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    old_downloads = YouTubeMP3.objects.filter(
        created_at__lt=cutoff_date,
        download_status__in=['completed', 'failed']
    )

    count = old_downloads.count()
    old_downloads.delete()

    return f"Cleaned up {count} old download records"
