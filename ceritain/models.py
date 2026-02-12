from django.conf import settings
from django.core.exceptions import ValidationError
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
    title = models.CharField(max_length=255, blank=True, null=True)
    content_text = models.TextField(blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=255, blank=True, null=True)
    final_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    
    input_token = models.IntegerField(default=0)
    output_token = models.IntegerField(default=0)
    total_token = models.IntegerField(default=0)
    result_file = models.FileField(upload_to='story_narration_results/', blank=True, null=True)
    message_response = models.TextField(blank=True, null=True)
    estimated_read_time = models.IntegerField(default=0)

    def clean(self):
        """Validate token quota before saving new StoryNarration."""
        super().clean()
        # Only validate on creation (when pk is None)
        if self.pk is None:
            narration_settings = StoryNarrationSettings.get_solo()
            if narration_settings.total_token_used >= narration_settings.daily_token_quota:
                raise ValidationError(
                    "Daily token quota exceeded. Please try again tomorrow."
                )

    def save(self, *args, **kwargs):
        """Override save to ensure clean() validation runs."""
        # Only run full_clean on creation to avoid issues with updates
        if self.pk is None:
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or ""

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
    AI_MODEL_CHOICES_TXT = (
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4.1-nano', 'GPT-4.1 Nano'),
    )
    ai_model = models.CharField(max_length=100, choices=AI_MODEL_CHOICES, default='gpt-4o-mini-tts', help_text="AI model to use for TTS")
    ai_model_txt = models.CharField(max_length=100, choices=AI_MODEL_CHOICES_TXT, default='gpt-4.1-nano', help_text="AI model to use for Generate Text")
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

