import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StoryNarration
from .serializers import (
    StoryNarrationCreateResponseSerializer,
    StoryNarrationCreateSerializer,
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
