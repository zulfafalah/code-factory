import os
import tempfile
import json
from pathlib import Path

import yt_dlp
from celery import shared_task
from django.conf import settings

from .models import YouTubeMP3


def get_youtube_cookies():
    """
    Get YouTube cookies for authentication.
    Returns cookie data in the format expected by yt-dlp.

    You can also set cookies via environment variables for production:
    - YOUTUBE_COOKIES_JSON: JSON string containing cookie data
    """
    # Check if cookies are provided via environment variable (recommended for production)
    env_cookies = os.environ.get('YOUTUBE_COOKIES_JSON')
    if env_cookies:
        try:
            return json.loads(env_cookies)
        except json.JSONDecodeError:
            pass  # Fall back to hardcoded cookies

    # Hardcoded cookies (update these when they expire)
    cookies_data = [
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701944,
            "hostOnly": False,
            "httpOnly": True,
            "name": "__Secure-3PSID",
            "path": "/",
            "sameSite": "no_restriction",
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "g.a000xwjJulgh1pYw7DGAa3xt0FvyJYAnELY_QLPV82yAl_mXPGrHqMDrp6W_cO6V3ozBsR0vCgACgYKAd4SARYSFQHGX2MiOLcQhA-0FOUnpVASpbFodBoVAUF8yKqb-79DU9BGdjb6685uUMV00076"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1781316693.220718,
            "hostOnly": False,
            "httpOnly": False,
            "name": "SIDCC",
            "path": "/",
            "sameSite": None,
            "secure": False,
            "session": False,
            "storeId": None,
            "value": "AKEyXzVboJOeH_7tSSPCMg8HO0pgov-Oy7fUNMT1E7RzJZMt3Y7Og06XWkjd2Yjk0mZGF8Bc"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701774,
            "hostOnly": False,
            "httpOnly": False,
            "name": "SID",
            "path": "/",
            "sameSite": None,
            "secure": False,
            "session": False,
            "storeId": None,
            "value": "g.a000xwjJulgh1pYw7DGAa3xt0FvyJYAnELY_QLPV82yAl_mXPGrHOz72bVaNHoSlIC3pKAU0ZgACgYKAZ8SARYSFQHGX2MiPNtLZwhIsAcg1EqGaoacLBoVAUF8yKqubiRATS7IXQdquxk8hKyz0076"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1781316693.220115,
            "hostOnly": False,
            "httpOnly": True,
            "name": "__Secure-1PSIDTS",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "sidts-CjEB5H03P35OVl4mVtCkiDckmbNOyqO4RAGn4DmLhPS6nOwmXomA9YWkGG7yGw0CLyiNEAA"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701483,
            "hostOnly": False,
            "httpOnly": False,
            "name": "SAPISID",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "OMds_al9HduG6JVO/AblHifgcTLteaayX5"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1781316693.220892,
            "hostOnly": False,
            "httpOnly": True,
            "name": "__Secure-1PSIDCC",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "AKEyXzVRsSLVleorbyLoTfiYmmE4J-VJJYYTYpWVPLxJyq5BtgsOKH28KcnnZrFmfZ8MUs2i"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701336,
            "hostOnly": False,
            "httpOnly": True,
            "name": "SSID",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "AF7kq19DRizzF6e83"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701581,
            "hostOnly": False,
            "httpOnly": False,
            "name": "__Secure-1PAPISID",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "OMds_al9HduG6JVO/AblHifgcTLteaayX5"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701873,
            "hostOnly": False,
            "httpOnly": True,
            "name": "__Secure-1PSID",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "g.a000xwjJulgh1pYw7DGAa3xt0FvyJYAnELY_QLPV82yAl_mXPGrH1p-BfT_kpzAgdCUX-YWRdAACgYKAUsSARYSFQHGX2MiljmyDkUSYc969KDfa9rjEhoVAUF8yKpl1R8vZ6xLLq3RDYw_3GNj0076"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701661,
            "hostOnly": False,
            "httpOnly": False,
            "name": "__Secure-3PAPISID",
            "path": "/",
            "sameSite": "no_restriction",
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "OMds_al9HduG6JVO/AblHifgcTLteaayX5"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1781316693.221045,
            "hostOnly": False,
            "httpOnly": True,
            "name": "__Secure-3PSIDCC",
            "path": "/",
            "sameSite": "no_restriction",
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "AKEyXzWZ-wUunjR2YlBtR8aa7XmnfEw4JIhu_oMP5nyqz2tlYANZG8Lcg9tldLuHB8x0Ch7P"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1781316693.220506,
            "hostOnly": False,
            "httpOnly": True,
            "name": "__Secure-3PSIDTS",
            "path": "/",
            "sameSite": "no_restriction",
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "sidts-CjEB5H03P35OVl4mVtCkiDckmbNOyqO4RAGn4DmLhPS6nOwmXomA9YWkGG7yGw0CLyiNEAA"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701395,
            "hostOnly": False,
            "httpOnly": False,
            "name": "APISID",
            "path": "/",
            "sameSite": None,
            "secure": False,
            "session": False,
            "storeId": None,
            "value": "Tva2Xe0XpPyU4sRu/AQ-j65j_pausFMNq0"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784281987.701275,
            "hostOnly": False,
            "httpOnly": True,
            "name": "HSID",
            "path": "/",
            "sameSite": None,
            "secure": False,
            "session": False,
            "storeId": None,
            "value": "AnQL8aECJYmmkRN52"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784282009.594806,
            "hostOnly": False,
            "httpOnly": True,
            "name": "LOGIN_INFO",
            "path": "/",
            "sameSite": "no_restriction",
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "AFmmF2swRAIgV9z75b2sao_9A1EsHtlCjIVyLXoUjj_ZIX8peMl1xPMCIEpf0ngV_e6kavJlPv4L_U0CNuCRv8OrFuTFs3FyPjcX:QUQ3MjNmeG5zRnBXS0ZMTVlkRGs0ZWR0NlJzYnAyU0h5YmpsVmFZOU1uU3EyclFpaXF2S2YzRmxvWUk5bHJDMXBDN3lwaFpQeFF4UDR1WDVhbUNodXJ6TVFXbHF2NVFqRktxTWdrNVVBOW9waThzeERQS2d1NmI3Z2p3TFBIY3JQQ2Q0V01uaDBoYnBLOUhad1lmMkNyYWlpMllkUVVFMlVB"
        },
        {
            "domain": ".youtube.com",
            "expirationDate": 1784282242.049034,
            "hostOnly": False,
            "httpOnly": False,
            "name": "PREF",
            "path": "/",
            "sameSite": None,
            "secure": True,
            "session": False,
            "storeId": None,
            "value": "f6=40000000&tz=Asia.Jakarta&f7=100"
        }
    ]    # Convert to a simpler format for easier processing
    simplified_cookies = []
    for cookie in cookies_data:
        simplified_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie['path'],
            'secure': cookie['secure'],
            'httponly': cookie.get('httpOnly', False),
            'expires': cookie.get('expirationDate')
        }
        simplified_cookies.append(simplified_cookie)

    return simplified_cookies


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
