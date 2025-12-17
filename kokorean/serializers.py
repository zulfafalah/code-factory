from rest_framework import serializers
from .models import Manhwa
from .utils import extract_image_urls_from_url
import json


class ManhwaSerializer(serializers.ModelSerializer):
    """
    Serializer for Manhwa model with all fields
    """
    class Meta:
        model = Manhwa
        fields = ['id', 'url', 'title', 'created_at', 'updated_at', 'download_status', 'content', 'zip_file']
        read_only_fields = ['id', 'created_at', 'updated_at', 'zip_file']


class ManhwaListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list view (without content field)
    """
    class Meta:
        model = Manhwa
        fields = ['id', 'url', 'title', 'created_at', 'updated_at', 'download_status', 'zip_file']
        read_only_fields = ['id', 'created_at', 'updated_at', 'zip_file']


class ManhwaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Manhwa with validation.
    Title is optional - it will be auto-extracted from the web page.
    """
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    
    class Meta:
        model = Manhwa
        fields = ['url', 'title', 'download_status', 'content']
    
    def validate_url(self, value):
        """
        Validate that URL is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("URL tidak boleh kosong")
        return value
    

    
    def create(self, validated_data):
        """
        Override create method to extract title and image URLs from URL,
        then trigger background task to download and compress images
        """
        from .tasks import download_and_compress_manhwa_images
        from urllib.parse import urlparse
        
        url = validated_data.get('url')
        
        # Extract title and image URLs from the provided URL
        result = extract_image_urls_from_url(url)
        
        if result['success']:
            # Update title with extracted title from web page
            validated_data['title'] = result['title']
            
            # Store image URLs as JSON in content field
            validated_data['content'] = json.dumps(result['image_urls'])
            # Set initial status to 'pending' (will be updated by background task)
            validated_data['download_status'] = 'pending'
        else:
            # If extraction fails, set status to 'failed' and store error message
            validated_data['download_status'] = 'failed'
            validated_data['content'] = json.dumps({
                'error': result.get('error', 'Unknown error')
            })
            # Use extracted title even if extraction failed
            if 'title' in result:
                validated_data['title'] = result['title']
        
        # Create the Manhwa instance
        instance = super().create(validated_data)
        
        # If extraction was successful, trigger background task to download images
        if result['success']:
            # Extract base URL from manhwa URL
            parsed_url = urlparse(url)
            base_url = "https://image.asfsadfimiim.com/"
            
            # Trigger Celery task asynchronously
            download_and_compress_manhwa_images.delay(
                manhwa_id=instance.id,
                base_url=base_url,
                max_workers=3
            )
        
        return instance




class ManhwaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Manhwa
    """
    class Meta:
        model = Manhwa
        fields = ['url', 'title', 'download_status', 'content']
        
    def validate_url(self, value):
        """
        Validate that URL is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("URL tidak boleh kosong")
        return value
    
    def validate_title(self, value):
        """
        Validate that title is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Title tidak boleh kosong")
        return value
