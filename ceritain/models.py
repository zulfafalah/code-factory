from django.conf import settings
from django.db import models

# Create your models here.
class StoryNarration(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=255)
    content_text = models.TextField()
    source_url = models.URLField(blank=True, null=True)
    final_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='storynarration_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='storynarration_updated')

    def __str__(self):
        return self.title