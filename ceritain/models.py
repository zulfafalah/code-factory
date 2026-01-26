from django.conf import settings
from django.db import models
from solo.models import SingletonModel

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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='storynarration_created', null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='storynarration_updated', null=True)
    
    input_token = models.IntegerField(default=0)
    output_token = models.IntegerField(default=0)
    total_token = models.IntegerField(default=0)
    result_file = models.FileField(upload_to='story_narration_results/', blank=True, null=True)
    message_response = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class StoryNarrationSettings(SingletonModel):
    """
    Singleton model for global Story Narration settings.
    Uses django-solo to ensure only one instance exists.
    """
    is_maintenance = models.BooleanField(default=False, help_text="Enable maintenance mode")
    daily_token_quota = models.IntegerField(default=100000, help_text="Daily token quota limit")
    AI_MODEL_CHOICES = (
        ('tts-1', 'TTS-1'),
        ('tts-1-hd', 'TTS-1 HD'),
        ('gpt-4o-mini-tts', 'GPT-4o Mini TTS'),
    )
    ai_model = models.CharField(max_length=100, choices=AI_MODEL_CHOICES, default='gpt-4o-mini-tts', help_text="AI model to use for TTS")
    total_token_used = models.IntegerField(default=0, help_text="Total tokens used")
    VOICE_CHOICES = (
        ('alloy', 'Alloy'),
        ('echo', 'Echo'),
        ('fable', 'Fable'),
        ('onyx', 'Onyx'),
        ('nova', 'Nova'),
        ('shimmer', 'Shimmer'),
    )
    voice_type = models.CharField(max_length=50, choices=VOICE_CHOICES, default='nova', help_text="Voice type for TTS")
    background_music = models.FileField(upload_to='background_music/', blank=True, null=True, help_text="Background music file")

    def __str__(self):
        return "Story Narration Settings"

    class Meta:
        verbose_name = "Story Narration Settings"
        verbose_name_plural = "Story Narration Settings"

