from pathlib import Path
import logging

from django.http import HttpResponse
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import YouTubeMP3
from .serializers import DownloadStartResponseSerializer
from .serializers import YouTubeMP3CreateSerializer
from .serializers import YouTubeMP3Serializer

# Set up logging
logger = logging.getLogger(__name__)


class YouTubeMP3ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for YouTube MP3 downloads.
    Provides list, retrieve operations and custom actions.
    """

    queryset = YouTubeMP3.objects.all().order_by("-created_at")
    serializer_class = YouTubeMP3Serializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List all downloads",
        description="Get a list of all YouTube MP3 downloads",
        tags=["YouTube Toolkit"],
        responses={200: YouTubeMP3Serializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get download details",
        description="Get details of a specific YouTube MP3 download",
        tags=["YouTube Toolkit"],
        responses={200: YouTubeMP3Serializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Download MP3 file",
        description="Download the actual MP3 file",
        tags=["YouTube Toolkit"],
        responses={
            200: "MP3 file content",
            404: "File not found or not ready",
        },
    )

    @action(detail=True, methods=["get"], url_path="download", url_name="download")
    def download(self, request, pk=None):
        """Download the actual MP3 file"""
        youtube_mp3 = self.get_object()

        if not youtube_mp3.is_downloadable:
            return Response(
                {"error": "File not found or not ready for download"},
                status=status.HTTP_404_NOT_FOUND,
            )

        file_path = Path(youtube_mp3.file_path)
        if not file_path.exists():
            return Response(
                {"error": "File not found on server"}, status=status.HTTP_404_NOT_FOUND
            )

        # Open and serve the file
        with file_path.open("rb") as f:
            response = HttpResponse(f.read(), content_type="audio/mpeg")
            content_disposition = f'attachment; filename="{youtube_mp3.file_name}"'
            response["Content-Disposition"] = content_disposition
            response["Content-Length"] = youtube_mp3.file_size
            return response


class DownloadStartAPIView(APIView):
    """
    API View to start YouTube MP3 downloads
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Start download",
        description="Start a new YouTube MP3 download",
        tags=["YouTube Toolkit"],
        request=YouTubeMP3CreateSerializer,
        responses={
            200: DownloadStartResponseSerializer,
            400: "Bad request",
            500: "Internal server error",
        },
    )
    def post(self, request):
        """Start a YouTube MP3 download"""
        serializer = YouTubeMP3CreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        video_url = serializer.validated_data["video_url"]

        try:
            # Create or get existing YouTubeMP3 instance
            youtube_mp3, created = YouTubeMP3.objects.get_or_create(
                video_url=video_url, defaults={"download_status": "pending"}
            )

            if created or youtube_mp3.download_status in ["pending", "failed"]:
                if not created:
                    # Reset for retry
                    youtube_mp3.download_status = "pending"
                    youtube_mp3.error_message = None
                    youtube_mp3.save()

                # Start the download task
                task = youtube_mp3.start_download()

                return Response(
                    {
                        "success": True,
                        "message": "Download started successfully",
                        "task_id": task.id,
                        "download_id": youtube_mp3.id,
                        "status": youtube_mp3.download_status,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "success": False,
                        "message": f"Download already exists with status: {youtube_mp3.download_status}",
                        "download_id": youtube_mp3.id,
                        "status": youtube_mp3.download_status,
                    },
                    status=status.HTTP_200_OK,
                )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CookieRefreshAPIView(APIView):
    """
    API endpoint to refresh YouTube cookies for authentication.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh YouTube cookies",
        description="Trigger a background task to refresh YouTube cookies for authentication",
        tags=["YouTube Toolkit"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "cookie_file": {
                        "type": "string",
                        "description": "Path to cookies.txt file (optional)"
                    },
                    "use_chromium": {
                        "type": "boolean",
                        "description": "Use Chromium browser instead of Chrome (default: false)"
                    },
                    "sync": {
                        "type": "boolean",
                        "description": "Run synchronously without Celery (default: false)"
                    },
                    "test_only": {
                        "type": "boolean",
                        "description": "Only test existing cookies without refreshing (default: false)"
                    }
                }
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "task_id": {"type": "string"},
                    "cookie_file": {"type": "string"},
                    "test_passed": {"type": "boolean"},
                    "auth_test_passed": {"type": "boolean"}
                }
            },
            400: {"description": "Bad request"},
            500: {"description": "Internal server error"}
        }
    )
    def post(self, request):
        """
        Refresh YouTube cookies via POST request.
        """
        try:
            # Get parameters from request
            cookie_file = request.data.get('cookie_file')
            use_chromium = request.data.get('use_chromium', False)
            sync_mode = request.data.get('sync', False)
            test_only = request.data.get('test_only', False)

            # Determine cookie file path
            if not cookie_file:
                cookie_file = getattr(settings, 'YOUTUBE_COOKIES_PATH', '/tmp/cookies.txt')

            logger.info(f"Cookie refresh requested: file={cookie_file}, chromium={use_chromium}, sync={sync_mode}, test_only={test_only}")

            if test_only:
                return self._test_cookies_only(cookie_file)

            if sync_mode:
                return self._run_sync(cookie_file, use_chromium)
            else:
                return self._run_async(cookie_file, use_chromium)

        except Exception as e:
            logger.error(f"Error in cookie refresh API: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Cookie refresh failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _test_cookies_only(self, cookie_file):
        """Test existing cookies without refreshing"""
        try:
            from .refresh_cookie import test_cookies, test_authenticated_access
            import os

            if not os.path.exists(cookie_file):
                return Response(
                    {
                        "success": False,
                        "error": f"Cookie file {cookie_file} not found!"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Test basic functionality
            test_result = test_cookies(cookie_file)

            # Test authenticated access
            auth_result = test_authenticated_access(cookie_file)

            return Response(
                {
                    "success": True,
                    "message": "Cookie testing completed",
                    "cookie_file": cookie_file,
                    "test_passed": test_result,
                    "auth_test_passed": auth_result,
                    "overall_status": "passed" if (test_result and auth_result) else "failed"
                },
                status=status.HTTP_200_OK
            )

        except ImportError as e:
            return Response(
                {
                    "success": False,
                    "error": f"Could not import refresh_cookie module: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error testing cookies: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _run_sync(self, cookie_file, use_chromium):
        """Run cookie refresh synchronously"""
        try:
            from .refresh_cookie import (
                update_cookies,
                test_cookies,
                test_authenticated_access,
                clean_expired_cookies
            )
            import os

            # Check if cookie file exists
            if not os.path.exists(cookie_file):
                # Create empty cookie file if it doesn't exist
                os.makedirs(os.path.dirname(cookie_file), exist_ok=True)
                with open(cookie_file, 'w') as f:
                    f.write("# Netscape HTTP Cookie File\n")
                    f.write("# Generated by cookie refresh API\n\n")
                logger.info(f"Created new cookie file: {cookie_file}")

            # Clean expired cookies first
            clean_expired_cookies(cookie_file)

            # Refresh cookies
            refresh_result = update_cookies(cookie_file, use_chromium)

            if not refresh_result:
                return Response(
                    {
                        "success": False,
                        "error": "Cookie refresh failed!"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Test the refreshed cookies
            test_result = test_cookies(cookie_file)
            auth_result = test_authenticated_access(cookie_file)

            # Final cleanup
            clean_expired_cookies(cookie_file)

            return Response(
                {
                    "success": True,
                    "message": "Cookies refreshed successfully (synchronous)",
                    "cookie_file": cookie_file,
                    "test_passed": test_result,
                    "auth_test_passed": auth_result,
                    "browser_used": "chromium" if use_chromium else "chrome"
                },
                status=status.HTTP_200_OK
            )

        except ImportError as e:
            return Response(
                {
                    "success": False,
                    "error": f"Could not import refresh_cookie module: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error during cookie refresh: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _run_async(self, cookie_file, use_chromium):
        """Run cookie refresh using Celery task"""
        try:
            from .tasks import refresh_youtube_cookies

            # Start the Celery task
            result = refresh_youtube_cookies.delay(cookie_file, use_chromium)

            return Response(
                {
                    "success": True,
                    "message": "Cookie refresh task scheduled successfully",
                    "task_id": result.id,
                    "cookie_file": cookie_file,
                    "browser_used": "chromium" if use_chromium else "chrome",
                    "note": "Task is running in background. Check task status using task_id."
                },
                status=status.HTTP_200_OK
            )

        except ImportError as e:
            return Response(
                {
                    "success": False,
                    "error": f"Could not import Celery task: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error scheduling async task: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get cookie refresh status",
        description="Get information about cookie file and authentication status",
        tags=["YouTube Toolkit"],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "cookie_file": {"type": "string"},
                    "exists": {"type": "boolean"},
                    "file_size": {"type": "integer"},
                    "last_modified": {"type": "string"}
                }
            }
        }
    )
    def get(self, request):
        """
        Get cookie status information.
        """
        try:
            import os
            from datetime import datetime

            cookie_file = request.query_params.get('cookie_file')
            if not cookie_file:
                cookie_file = getattr(settings, 'YOUTUBE_COOKIES_PATH', '/tmp/cookies.txt')

            file_info = {
                "cookie_file": cookie_file,
                "exists": os.path.exists(cookie_file)
            }

            if file_info["exists"]:
                stat = os.stat(cookie_file)
                file_info["file_size"] = stat.st_size
                file_info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

                # Count cookies
                try:
                    with open(cookie_file, 'r') as f:
                        lines = f.readlines()
                    cookie_count = len([line for line in lines if line.strip() and not line.startswith('#')])
                    file_info["cookie_count"] = cookie_count
                except Exception:
                    file_info["cookie_count"] = "unknown"

            return Response(file_info, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error getting cookie status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
