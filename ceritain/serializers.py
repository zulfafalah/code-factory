from rest_framework import serializers
from urllib.parse import urlparse

from .models import StoryNarration


class StoryNarrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new StoryNarration"""
    
    content_text = serializers.CharField(required=False, allow_blank=True, help_text="Content text for narration (required if source_url is not provided)")
    source_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, help_text="Source URL (optional)")
    
    class Meta:
        model = StoryNarration
        fields = ["content_text", "source_url"]
    
    def validate_content_text(self, value):
        """Validate that content_text is not empty unless source_url is provided"""
        source_url = self.initial_data.get('source_url')
        
        # If source_url is provided, content_text can be empty
        if source_url:
            return value.strip() if value else ""
        
        # If source_url is not provided, content_text must not be empty
        if not value or not value.strip():
            raise serializers.ValidationError("Content text cannot be empty when source_url is not provided")
        
        return value.strip()
    
    def validate_source_url(self, value):
        """
        Validate that the URL is from Medium and manipulate it to use Freedium mirror.
        
        Rules:
        1. If URL host is not freedium-mirror.cfd, wrap it with https://freedium-mirror.cfd/{url}
        2. If URL is not from Medium, reject it
        """
        if not value:
            return value
        
        # Parse the original URL
        parsed_url = urlparse(value)
        hostname = parsed_url.hostname
        
        if not hostname:
            raise serializers.ValidationError("Invalid URL format")
        
        # Check if already using Freedium mirror
        if hostname == "freedium-mirror.cfd":
            # Extract the original URL from Freedium format
            # Format: https://freedium-mirror.cfd/https://medium.com/...
            path = parsed_url.path.lstrip('/')
            if path.startswith('http'):
                original_url = path
                original_hostname = urlparse(original_url).hostname
            else:
                raise serializers.ValidationError("Invalid Freedium mirror URL format")
        else:
            # Not using Freedium mirror yet
            original_url = value
            original_hostname = hostname
        
        # Validate that the original URL is from Medium
        if not (original_hostname == "medium.com" or original_hostname.endswith(".medium.com")):
            raise serializers.ValidationError("URL must be from Medium (medium.com or its subdomains)")
        
        # If not already using Freedium mirror, wrap it
        if hostname != "freedium-mirror.cfd":
            return f"https://freedium-mirror.cfd/{value}"
        
        return value


class StoryNarrationSerializer(serializers.ModelSerializer):
    """Serializer for StoryNarration model"""
    
    source_url = serializers.SerializerMethodField()
    estimated_read_time_formatted = serializers.SerializerMethodField()
    
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
            "estimated_read_time",
            "estimated_read_time_formatted",
            "play_count",
            "background_cover",
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
    
    def get_source_url(self, obj):
        """Remove freedium-mirror.cfd prefix from source_url"""
        if not obj.source_url:
            return obj.source_url
        
        # Remove the freedium mirror prefix if present
        freedium_prefix = "https://freedium-mirror.cfd/"
        if obj.source_url.startswith(freedium_prefix):
            return obj.source_url[len(freedium_prefix):]
        
        return obj.source_url
    
    def get_estimated_read_time_formatted(self, obj):
        """Format estimated_read_time as 'X Min' or 'X Sec'"""
        if obj.estimated_read_time == 0:
            return "0 Sec"
        
        # Convert seconds to minutes
        minutes = obj.estimated_read_time // 60
        
        if minutes > 0:
            return f"{minutes} Min"
        else:
            return f"{obj.estimated_read_time} Sec"
    




class StoryNarrationCreateResponseSerializer(serializers.Serializer):
    """Serializer for create story narration response"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    task_id = serializers.CharField(required=False)
    story_narration_id = serializers.CharField(required=False)
    status = serializers.CharField(required=False)


class StoryNarrationListSerializer(serializers.ModelSerializer):
    """Serializer for listing StoryNarration with optimized fields"""
    
    content_text_preview = serializers.SerializerMethodField()
    estimated_read_time_formatted = serializers.SerializerMethodField()
    
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
            "created_by",
            "play_count",
            "estimated_read_time",
            "estimated_read_time_formatted",
            "background_cover"
        ]
        read_only_fields = fields
    
    def get_content_text_preview(self, obj):
        """Return first 200 characters of content_text"""
        if obj.content_text and len(obj.content_text) > 200:
            return obj.content_text[:200] + "..."
        return obj.content_text
    
    def get_estimated_read_time_formatted(self, obj):
        """Format estimated_read_time as 'X Min' or 'X Sec'"""
        if obj.estimated_read_time == 0:
            return "0 Sec"
        
        # Convert seconds to minutes
        minutes = obj.estimated_read_time // 60
        
        if minutes > 0:
            return f"{minutes} Min"
        else:
            return f"{obj.estimated_read_time} Sec"
    

