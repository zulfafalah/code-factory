import os
import tempfile
import json
from pathlib import Path

import yt_dlp
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import YouTubeMP3


def get_youtube_cookies():
    """
    Get YouTube cookies for authentication from the database.
    Returns cookie data in the format expected by yt-dlp.

    Fallback options:
    1. Database (Cookie model with application='youtube')
    2. Environment variable YOUTUBE_COOKIES_JSON
    3. Empty list (no authentication)
    """
    try:
        # Import here to avoid circular imports
        from master.models import Cookie

        # Get active YouTube cookies from database
        youtube_cookies = Cookie.objects.filter(
            application='youtube',
            is_active=True
        ).exclude(
            expires_at__lt=timezone.now()  # Exclude expired cookies
        ).order_by('-created_at').first()  # Get the most recent one

        if youtube_cookies and youtube_cookies.cookie_data:
            # Extract cookie data from the model
            cookies_data = youtube_cookies.cookie_data

            # Handle both list and dict formats
            if isinstance(cookies_data, dict):
                # If it's a single cookie object, convert to list
                cookies_data = [cookies_data]
            elif not isinstance(cookies_data, list):
                # If it's neither list nor dict, skip to fallback
                cookies_data = []

            # Convert to a simpler format for easier processing
            simplified_cookies = []
            for cookie in cookies_data:
                if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                    simplified_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.youtube.com'),
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', True),
                        'httponly': cookie.get('httpOnly', False),
                        'expires': cookie.get('expirationDate', cookie.get('expires'))
                    }
                    simplified_cookies.append(simplified_cookie)

            if simplified_cookies:
                print(f"Using {len(simplified_cookies)} YouTube cookies from database")
                return simplified_cookies

    except Exception as e:
        print(f"Error loading cookies from database: {e}")

    # Check if cookies are provided via environment variable (fallback)
    env_cookies = os.environ.get('YOUTUBE_COOKIES_JSON')
    if env_cookies:
        try:
            cookies_data = json.loads(env_cookies)
            if isinstance(cookies_data, list):
                simplified_cookies = []
                for cookie in cookies_data:
                    simplified_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.youtube.com'),
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', True),
                        'httponly': cookie.get('httpOnly', False),
                        'expires': cookie.get('expirationDate', cookie.get('expires'))
                    }
                    simplified_cookies.append(simplified_cookie)
                print(f"Using {len(simplified_cookies)} YouTube cookies from environment variable")
                return simplified_cookies
        except json.JSONDecodeError:
            print("Invalid JSON format in YOUTUBE_COOKIES_JSON environment variable")

    # No cookies available - return empty list
    print("No YouTube cookies available - proceeding without authentication")
    return []


def create_cookie_file(temp_dir):
    """
    Create a temporary cookie file for yt-dlp in Netscape format.
    Returns the path to the cookie file.
    """
    try:
        cookies_data = get_youtube_cookies()
        cookie_file_path = os.path.join(temp_dir, "youtube_cookies.txt")

        with open(cookie_file_path, 'w') as f:
            # Write Netscape cookie file header
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This is a generated file! Do not edit.\n\n")

            # Convert each cookie to Netscape format
            for cookie in cookies_data:
                # Netscape format: domain\tinclude_subdomains\tpath\tsecure\texpiration\tname\tvalue
                domain = cookie['domain']
                include_subdomains = "TRUE" if domain.startswith('.') else "FALSE"
                path = cookie['path']
                secure = "TRUE" if cookie['secure'] else "FALSE"
                expiration = str(int(cookie.get('expires', 0))) if cookie.get('expires') else "0"
                name = cookie['name']
                value = cookie['value']

                line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n"
                f.write(line)

        return cookie_file_path
    except Exception as e:
        # If cookie file creation fails, return None to proceed without cookies
        print(f"Warning: Could not create cookie file: {e}")
        return None


@shared_task(bind=True)
def download_youtube_mp3(self, youtube_mp3_id):
    """
    Celery task to download YouTube video as MP3.

    Args:
        youtube_mp3_id: ID of the YouTubeMP3 model instance
    """
    try:
        # Add a small delay to ensure database transaction is committed
        import time
        time.sleep(1)

        # Get the YouTubeMP3 instance
        try:
            youtube_mp3 = YouTubeMP3.objects.get(id=youtube_mp3_id)
        except YouTubeMP3.DoesNotExist:
            # Log more details for debugging
            print(f"DEBUG: YouTubeMP3 with id {youtube_mp3_id} not found")
            print(f"DEBUG: Available IDs: {list(YouTubeMP3.objects.values_list('id', flat=True))}")
            return {
                "status": "error",
                "message": f"YouTubeMP3 with id {youtube_mp3_id} not found. Available IDs: {list(YouTubeMP3.objects.values_list('id', flat=True))}"
            }

        youtube_mp3.download_status = "in_progress"
        youtube_mp3.save()

        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create cookie file for YouTube authentication
            cookie_file_path = create_cookie_file(temp_dir)

            # Configure yt-dlp options with cookies
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "writesubtitles": False,
                "writeautomaticsub": False,
                "ignoreerrors": False,
                # Additional options for better YouTube support
                "extractor_retries": 3,
                "http_headers": {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }

            # Add cookie file if it was created successfully
            if cookie_file_path:
                ydl_opts["cookiefile"] = cookie_file_path

            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get video details
                info = ydl.extract_info(youtube_mp3.video_url, download=False)
                video_title = info.get("title", "Unknown")

                # Update the model with video info
                youtube_mp3.video_title = video_title
                youtube_mp3.save()

                # Now download the video
                ydl.download([youtube_mp3.video_url])

                # Find the downloaded MP3 file
                mp3_files = list(Path(temp_dir).glob("*.mp3"))
                if mp3_files:
                    mp3_file = mp3_files[0]
                    file_size = mp3_file.stat().st_size

                    # Create media directory for downloads if it doesn't exist
                    import re
                    import shutil

                    from django.conf import settings

                    download_dir = Path(settings.MEDIA_ROOT) / "yttoolkit" / "downloads"
                    download_dir.mkdir(parents=True, exist_ok=True)

                    # Generate a safe filename
                    safe_filename = re.sub(r"[^\w\s-]", "", video_title)
                    safe_filename = re.sub(r"[-\s]+", "-", safe_filename)
                    final_filename = f"{safe_filename}_{youtube_mp3.id}.mp3"
                    final_path = download_dir / final_filename

                    # Copy the file to the media directory
                    shutil.copy2(mp3_file, final_path)

                    # Update model with file info
                    youtube_mp3.file_size = file_size
                    youtube_mp3.file_name = final_filename
                    youtube_mp3.file_path = str(final_path)

        # Mark as completed
        youtube_mp3.download_status = "completed"
        youtube_mp3.save()

        return {
            "status": "success",
            "message": f"Successfully downloaded: {video_title}",
            "file_size": youtube_mp3.file_size,
            "file_name": youtube_mp3.file_name,
        }

    except YouTubeMP3.DoesNotExist:
        return {
            "status": "error",
            "message": f"YouTubeMP3 with id {youtube_mp3_id} not found",
        }

    except yt_dlp.DownloadError as e:
        # Handle download errors
        try:
            youtube_mp3 = YouTubeMP3.objects.get(id=youtube_mp3_id)
            youtube_mp3.download_status = "failed"
            youtube_mp3.error_message = str(e)
            youtube_mp3.save()
        except YouTubeMP3.DoesNotExist:
            pass

        return {"status": "error", "message": f"Download failed: {str(e)}"}

    except Exception as e:
        # Handle any other errors
        try:
            youtube_mp3 = YouTubeMP3.objects.get(id=youtube_mp3_id)
            youtube_mp3.download_status = "failed"
            youtube_mp3.error_message = str(e)
            youtube_mp3.save()
        except YouTubeMP3.DoesNotExist:
            pass

        # Retry the task up to 3 times with exponential backoff
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2**self.request.retries), exc=e)

        return {"status": "error", "message": f"Task failed after retries: {str(e)}"}

    except YouTubeMP3.DoesNotExist:
        # This should now be handled in the beginning of the function
        return {
            "status": "error",
            "message": f"YouTubeMP3 with id {youtube_mp3_id} not found",
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
        created_at__lt=cutoff_date, download_status__in=["completed", "failed"]
    )

    count = old_downloads.count()
    old_downloads.delete()

    return f"Cleaned up {count} old download records"
