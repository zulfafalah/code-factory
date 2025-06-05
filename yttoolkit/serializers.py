from rest_framework import serializers

from .models import YouTubeMP3


class YouTubeMP3Serializer(serializers.ModelSerializer):
    """Serializer for YouTubeMP3 model"""

    file_size_mb = serializers.ReadOnlyField()
    is_downloadable = serializers.ReadOnlyField()
    download_url = serializers.ReadOnlyField(source="get_download_url")

    class Meta:
        model = YouTubeMP3
        fields = [
            "id",
            "video_url",
            "video_title",
            "download_status",
            "file_name",
            "file_size",
            "file_size_mb",
            "error_message",
            "created_at",
            "updated_at",
            "is_downloadable",
            "download_url",
        ]
        read_only_fields = [
            "id",
            "video_title",
            "download_status",
            "file_name",
            "file_size",
            "file_size_mb",
            "error_message",
            "created_at",
            "updated_at",
            "is_downloadable",
            "download_url",
        ]


class YouTubeMP3CreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new YouTubeMP3 downloads"""

    class Meta:
        model = YouTubeMP3
        fields = ["video_url"]

    def validate_video_url(self, value):
        """Validate YouTube URL"""
        if not value.startswith(("http://", "https://")):
            invalid_url_msg = "Invalid URL: Must start with 'http' or 'https'"
            raise serializers.ValidationError(invalid_url_msg)

        # You can add more specific YouTube URL validation here if needed
        if "youtube.com" not in value and "youtu.be" not in value:
            invalid_youtube_msg = "Please provide a valid YouTube URL"
            raise serializers.ValidationError(invalid_youtube_msg)

        return value


class DownloadStartResponseSerializer(serializers.Serializer):
    """Serializer for download start response"""

    success = serializers.BooleanField()
    message = serializers.CharField()
    task_id = serializers.CharField(required=False)
    download_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
