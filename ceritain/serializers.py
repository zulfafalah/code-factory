from rest_framework import serializers

from .models import StoryNarration


class StoryNarrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new StoryNarration"""
    
    content_text = serializers.CharField(required=True, help_text="Content text for narration (required)")
    source_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, help_text="Source URL (optional)")
    
    class Meta:
        model = StoryNarration
        fields = ["content_text", "source_url"]
    
    def validate_content_text(self, value):
        """Validate that content_text is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Content text cannot be empty")
        return value.strip()


class StoryNarrationSerializer(serializers.ModelSerializer):
    """Serializer for StoryNarration model"""
    
    class Meta:
        model = StoryNarration
        fields = [
            "id",
            "status",
            "title",
            "content_text",
            "source_url",
            "final_content",
            "created_at",
            "updated_at",
            "input_token",
            "output_token",
            "total_token",
            "result_file",
            "message_response",
        ]
        read_only_fields = [
            "id",
            "status",
            "title",
            "final_content",
            "created_at",
            "updated_at",
            "input_token",
            "output_token",
            "total_token",
            "result_file",
            "message_response",
        ]


class StoryNarrationCreateResponseSerializer(serializers.Serializer):
    """Serializer for create story narration response"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    task_id = serializers.CharField(required=False)
    story_narration_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)


class StoryNarrationListSerializer(serializers.ModelSerializer):
    """Serializer for listing StoryNarration with optimized fields"""
    
    content_text_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryNarration
        fields = [
            "id",
            "status",
            "title",
            "content_text_preview",
            "source_url",
            "created_at",
            "updated_at",
            "total_token",
            "result_file",
        ]
        read_only_fields = fields
    
    def get_content_text_preview(self, obj):
        """Return first 200 characters of content_text"""
        if obj.content_text and len(obj.content_text) > 200:
            return obj.content_text[:200] + "..."
        return obj.content_text

