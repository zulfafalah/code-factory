from pathlib import Path

from django.http import HttpResponse
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
        responses={200: YouTubeMP3Serializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get download details",
        description="Get details of a specific YouTube MP3 download",
        responses={200: YouTubeMP3Serializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Download MP3 file",
        description="Download the actual MP3 file",
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
