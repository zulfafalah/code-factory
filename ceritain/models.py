import random
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from solo.models import SingletonModel

# Default background cover images pool
BACKGROUND_COVER_IMAGES = [
    "https://lh3.googleusercontent.com/aida-public/AB6AXuASXQ0A_d2mJX-AV5VGiaAauguL9perBvjqHZe33Th2h-XxhgSoTpnt50z1E82r2kRopnk_wWcqJ9J_ZsZX_iTijmsKA6ZvX08o3nNFJzmh2tdFhmU8D-KORe7vpEN2k344tcY9VKWaclmHrrbJy-9gvPL1hfzg6wluFOMUTZc_z9De7IX0N0JAxbncToUcJwclMUdmMc-NCNjCxl_lSrHeymeZmA0NxhFptcZkVytoqwH_-wYpSDwkL20d7wHF_hTjbLedh6GVbQ",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBhffgmtTFcSyxqOWxS9NpVZIx2fW5m1ee2HxMITp2OUKF-vIpghLC1csAbxdSonw-nQ8PYNHpt-4rFQbyg4GUihTk4rnt-A8QSWfNLhjZ_aUNG63WWeA8qf6JtKq-ynU0uf7u9eSmGeqghgjlMS1Pvb55isr-VipwKoPCIPa-06IPUQAoFS1QKl9m8FjyljvqsTirQNjGIW5B21iDIipbKIUb4OucX4T8xPnqqNbQd-bNa0V0rBBycrJWdezROrwKvUDgmIXzl3g",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDMzP4g8fzKNQ7YlXgQ8r4aKG2hVM5nB3c6L9jR3Wx2j-YxiQToVtmo60y2F93s3lStam_wXdrK0oK_YtAy_kUjkntLA7ZwY19p4oOGKamj3ueGinV9E-MPSf8wsGO3s455udZ0WLXbdmnisstKz-0hwQM2jgah7xmvGPNVUad_a0Ef8JY1O1KBzcodUpVdKxdmNVenNd-ODooDym_mTsIfznfAnB1NyjGqudalnWuprzI_-xZqTExlsM1e8xIG_iUkc",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuCngjhnuUGdTzyrPXyT0s5bLJy3gX6o2ff3MyNJUq3PPVLG-WjqhiMD2dtBcyeEpox-oR9QZIqu-5sGRczhgGVjilU5rsu-B9RTXgOLikag_bVOH74XWeB9rg7uLr-0oV1vg8a0fTnHfrhjhkmNT2Qwc66jtus-WjqxLQDJQb-17JQVRBpGT2RL0n9DHjzlkwrtUjsROkHJX6C32jEJjqcLJVc5PvdY5U9yQorrOcRe-cObV",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBjgginvVHeUa0sQYzU1t6cMK04hY7p3gg4N0OKVr4QQWMH-XkrijNE3euCd0fFqpy-pS0RaJrv-6tHSd0ihHWkjmV6stv-C0SU0hPMjlbh-cWPG85YXfC0s7hvMs-1pW2wi9b1gUoIgsikiln0U3Rxd77kuvt-XksyMREM_c-28KRWSCqHU3SM1o0EIk0mlxsuVktTPmIKY7D43kFKkrdMKWd6QwdZ6V0zRpssPdSf-dPc",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuAkghjowWIfVb1tRZ0V2u7dNL15iZ8q4hh5O1PLWs5RRXNI-YlskjOF4fvDe1gGrqz-qT1ScKsw-7uITe1jiGXljnW7tuw-D1TV1iQNkmci-dXQH96ZYgD1t8iwNt-2qX3xj0c2hVpJhtjljm01V4Sye88lvwu-YktzNSFN_d-39LSXTDrIV4TN2p1FJl1nmytvWluUQnJLZ8E54lGLlsePLXe7RxeZ7W1zSqttQeSg-eQd",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBlhhkpxXJgWc2uSa1W3v8eOM26ja9r5ii6P2QMXt6SSYOJ-ZmtlkPG5gwEf2hHsrA-rU2TdLtx-8vJUf2kjHYmkoX8uvx-E2UW2jRO0nd_eYRH07aafB2ug9jxOu-3rY4yk1d3iWqKiukmlng2W5Tze99mwxv-ZluuOTGO_e-40MTYUEsJW5UO3q2GKm2onzvwXmvVRoKMaZG65mHMmsf0MYf8SyeJ8X2zTruuRfTi-fRe",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuCmiilqyYKhXd3vTb2X4w9fPN37kb0s6jj7Q3RNYu7TTZPK-anutlQH6hxFg3iItsc-sV3UeM4y-9wKVg3lkIZnlpY9vwy-F3VX3kSP1oe_faUI18bbcD3vh0kyPv-4sZ5zl2e4jXrLjvlnmoh3X6U0f00nxyq-amuuPUHP_f-51NUZVFtKX6VP4r3HLn3po0uwYnwWSp0NbZH76nINntg1NYg9TzfK9Y3zUsvvSgUk-gSf",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDnjjlrzZLiYe4wUc3Y5x0gQO48lc1t7kk8R4SObv8UUAQM-bouumRJ7hyGh4jJutd-tW4VfN5z-01LWh4mlJaompZ0wyz-G4WY4lTQ2pf_gcVK29ccdE4wi1l0Qw-5ta60m3f5kYsZtLPpuqOZZ_l3m22p0zs-cnwwRXKR_i-73QYbbHwLZ8YR6u5JNo5rr2xyawxz3r2QdcK98p0RqvlAQbl2V0hM0b6B1vyyXjXn-i",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuEokklsaaaMjZg5xVd4a6y1hRP59md2u8ll9S5TPc9VVBRL-cpvvnSK8izHi5kKvue-uX5WgO6A-12MXi5nmKbpnqa1x0A-H5XZ5mUR3qg_hdWL30ddeFEL5jm2Rx-6ub71n4g6lZtMakqyvr1PaAmr4n33q1u-dowwSYLS_j-84RZccIxMa9ZS7v6KOp6ss3yzby_w4s3RhdL09q1SrwmBR_mbW1iN1c7B2my0YkYo-j",
]

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
    play_count = models.IntegerField(default=0)
    background_cover = models.TextField(blank=True, null=True)

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
        """Override save to ensure clean() validation runs and assign default background."""
        # Only run full_clean on creation to avoid issues with updates
        if self.pk is None:
            self.full_clean()
        
        # Assign random background cover if not set
        if not self.background_cover:
            self.background_cover = random.choice(BACKGROUND_COVER_IMAGES)
        
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

