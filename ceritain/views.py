import logging
import mimetypes
import os

from django.db.models import F

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
    
    Accepts optional X-Client-Fingerprint header to track who created the narration.
    The header is processed by ClientFingerprintMiddleware.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Create Story Narration",
        description="Create a new Story Narration with content text and optional source URL. "
                    "Optionally include X-Client-Fingerprint header to track the creator.",
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

        # Get client fingerprint from middleware (attached to request)
        client_fingerprint = getattr(request, 'client_fingerprint', None)

        try:
            # Create StoryNarration instance
            story_narration = StoryNarration.objects.create(
                content_text=content_text,
                source_url=source_url,
                status="processing",
                created_by=client_fingerprint,
            )

            # Start the background processing task
            task = process_story_narration_task.delay(str(story_narration.pk))

            return Response(
                {
                    "success": True,
                    "message": "Story narration created and processing started",
                    "task_id": task.id,
                    "story_narration_id": str(story_narration.pk),
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
    
    Accepts optional X-Client-Fingerprint header (processed by middleware).
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
            story_narration = StoryNarration.objects.get(pk=story_narration_id)
            serializer = StoryNarrationSerializer(story_narration, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except StoryNarration.DoesNotExist:
            return Response(
                {"error": f"Story Narration with ID {story_narration_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class StoryNarrationStreamingAPIView(APIView):
    """
    API View to stream audio file from StoryNarration
    
    Accepts optional X-Client-Fingerprint header (processed by middleware).
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
            story_narration = StoryNarration.objects.get(pk=story_narration_id)

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

            # Increment play count atomically
            StoryNarration.objects.filter(pk=story_narration_id).update(
                play_count=F('play_count') + 1
            )

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
    
    Accepts optional X-Client-Fingerprint header (processed by middleware).
    
    Supports:
    - Search: ?search=<keyword> - searches in title, content_text, source_url, created_by email
    - Ordering: ?ordering=<field> - order by created_at, updated_at, status, title, total_token, created_by
      Use -<field> for descending order (e.g., ?ordering=-created_at)
    - Status filter: ?status=<status> - filter by status (draft, processing, done, failed)
    - Created by filter: ?created_by=<user_id> - filter by created_by user ID
    """

    permission_classes = [AllowAny]
    serializer_class = StoryNarrationListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "content_text", "source_url"]
    ordering_fields = ["created_at", "updated_at", "status", "title", "total_token", "created_by"]
    ordering = ["-created_at"]  # Default ordering

    @extend_schema(
        summary="List Story Narrations",
        description="Get list of Story Narrations with search and ordering support. "
                    "Use ?search=<keyword> to search in title, content_text, source_url, created_by email. "
                    "Use ?ordering=<field> to order results (prefix with - for descending). "
                    "Use ?status=<status> to filter by status. "
                    "Use ?created_by=<user_id> to filter by user who created the narration.",
        tags=["Ceritain"],
        responses={
            200: StoryNarrationListSerializer(many=True),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = StoryNarration.objects.all()
        
        # Filter by created_by if provided
        created_by_filter = self.request.query_params.get("created_by")
        if created_by_filter:
            queryset = queryset.filter(created_by=created_by_filter)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class StoryNarrationTrendingAPIView(generics.ListAPIView):
    """
    API View to get trending StoryNarrations.
    Returns top 5 stories ordered by play_count (highest first).
    """

    permission_classes = [AllowAny]
    serializer_class = StoryNarrationListSerializer

    @extend_schema(
        summary="Trending Story Narrations",
        description="Get top 5 trending Story Narrations ordered by play_count descending.",
        tags=["Ceritain"],
        responses={
            200: StoryNarrationListSerializer(many=True),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return StoryNarration.objects.filter(status="done").order_by("-play_count")[:10]

