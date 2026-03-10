import uuid
from django.db import models

class SocialComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.TextField(blank=True, null=True)
    platform = models.CharField(max_length=255, blank=True, null=True, choices=[
        ('tiktok', 'Tiktok'),
        ('instagram', 'Instagram'),
        ('youtube', 'Youtube'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('other', 'Other'),
    ])
    nickname = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    external_uid = models.CharField(max_length=255, blank=True, null=True)
    external_unique_id = models.CharField(max_length=255, blank=True, null=True)
    
    avatar_uri = models.CharField(max_length=255, blank=True, null=True)
    avatar_url_list = models.JSONField(blank=True, null=True)
    avatar_url_prefix = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    