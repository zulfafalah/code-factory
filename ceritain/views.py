import logging
import mimetypes
import os

from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StoryNarration
from .serializers import (
    StoryNarrationCreateResponseSerializer,
    StoryNarrationCreateSerializer,
    StoryNarrationListSerializer,
    StoryNarrationSerializer,
)
from .tasks import process_story_narration_task

logger = logging.getLogger(__name__)


class StoryNarrationCreateAPIView(APIView):
    """
    API View to create StoryNarration
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Create Story Narration",
        description="Create a new Story Narration with content text and optional source URL",
        tags=["Ceritain"],
        request=StoryNarrationCreateSerializer,
        responses={
            201: StoryNarrationCreateResponseSerializer,
            400: "Bad request",
            500: "Internal server error",
        },
    )
    def post(self, request):
        """Create a new StoryNarration"""
        serializer = StoryNarrationCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        content_text = serializer.validated_data["content_text"]
        source_url = serializer.validated_data.get("source_url")

        try:
            # Create StoryNarration instance
            story_narration = StoryNarration.objects.create(
                content_text=content_text,
                source_url=source_url,
                status="processing",
                created_by=request.user if request.user.is_authenticated else None,
            )

            # Start the background processing task
            task = process_story_narration_task.delay(story_narration.id)

            return Response(
                {
                    "success": True,
                    "message": "Story narration created and processing started",
                    "task_id": task.id,
                    "story_narration_id": story_narration.id,
                    "status": story_narration.status,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("Error creating StoryNarration")
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StoryNarrationStatusAPIView(APIView):
    """
    API View to check the status/progress of StoryNarration
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get Story Narration Status",
        description="Check the progress/status of a Story Narration by ID",
        tags=["Ceritain"],
        responses={
            200: StoryNarrationSerializer,
            404: "Story Narration not found",
        },
    )
    def get(self, request, story_narration_id):
        """Get the status of a StoryNarration"""
        try:
            story_narration = StoryNarration.objects.get(id=story_narration_id)
            
            response_data = {
                "id": story_narration.id,
                "status": story_narration.status,
                "title": story_narration.title,
                "content_text": story_narration.content_text[:200] + "..." if len(story_narration.content_text) > 200 else story_narration.content_text,
                "source_url": story_narration.source_url,
                "final_content": story_narration.final_content,
                "created_at": story_narration.created_at,
                "updated_at": story_narration.updated_at,
                "input_token": story_narration.input_token,
                "output_token": story_narration.output_token,
                "total_token": story_narration.total_token,
                "result_file": request.build_absolute_uri(story_narration.result_file.url) if story_narration.result_file else None,
                "message_response": story_narration.message_response,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        except StoryNarration.DoesNotExist:
            return Response(
                {"error": f"Story Narration with ID {story_narration_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class StoryNarrationStreamingAPIView(APIView):
    """
    API View to stream audio file from StoryNarration
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Stream Story Narration Audio",
        description="Stream the audio file from a completed Story Narration by ID",
        tags=["Ceritain"],
        responses={
            200: {"type": "string", "format": "binary", "description": "Audio file stream"},
            404: "Story Narration not found or no audio file available",
        },
    )
    def get(self, request, story_narration_id):
        """Stream the audio file from a StoryNarration"""
        try:
            story_narration = StoryNarration.objects.get(id=story_narration_id)

            # Check if result_file exists
            if not story_narration.result_file:
                return Response(
                    {"error": f"No audio file available for Story Narration ID {story_narration_id}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the file path
            file_path = story_narration.result_file.path

            # Check if file exists on disk
            if not os.path.exists(file_path):
                return Response(
                    {"error": "Audio file not found on server"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "audio/mpeg"  # Default to mp3

            # Get file name for Content-Disposition header
            file_name = os.path.basename(file_path)

            # Return streaming response
            response = FileResponse(
                open(file_path, "rb"),
                content_type=content_type,
            )
            response["Content-Disposition"] = f'inline; filename="{file_name}"'
            response["Accept-Ranges"] = "bytes"

            return response

        except StoryNarration.DoesNotExist:
            return Response(
                {"error": f"Story Narration with ID {story_narration_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class StoryNarrationListAPIView(generics.ListAPIView):
    """
    API View to list StoryNarration with filter and ordering support.
    
    Supports:
    - Search: ?search=<keyword> - searches in title, content_text, source_url
    - Ordering: ?ordering=<field> - order by created_at, updated_at, status, title, total_token
      Use -<field> for descending order (e.g., ?ordering=-created_at)
    - Status filter: ?status=<status> - filter by status (draft, processing, done, failed)
    """

    permission_classes = [AllowAny]
    serializer_class = StoryNarrationListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "content_text", "source_url"]
    ordering_fields = ["created_at", "updated_at", "status", "title", "total_token"]
    ordering = ["-created_at"]  # Default ordering

    @extend_schema(
        summary="List Story Narrations",
        description="Get list of Story Narrations with search and ordering support. "
                    "Use ?search=<keyword> to search in title, content_text, source_url. "
                    "Use ?ordering=<field> to order results (prefix with - for descending). "
                    "Use ?status=<status> to filter by status.",
        tags=["Ceritain"],
        responses={
            200: StoryNarrationListSerializer(many=True),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = StoryNarration.objects.all()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

