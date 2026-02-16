from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import StoryNarration, StoryNarrationSettings
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _

# Register your models here.

@admin.register(StoryNarration)
class StoryNarrationAdmin(ModelAdmin):
    list_display = ["title", "status", "created_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by", "status", "input_token", "output_token", "total_token", "result_file", "message_response", "estimated_read_time"]  

    def save_model(self, request, obj, form, change):   
        if not change:  # Creating a new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    fieldsets = (
        ("General", {
            "fields": (
                "content_text",
                "title",
                "source_url",
                "final_content",
                "status",
                "result_file",
                "estimated_read_time",
                "play_count",
            ),
            "classes": ("tabs",),
        }),
        ("Message Response", {
            "fields": (
                "message_response",
            ),
            "classes": ("tabs",),
        }),
        ("Created By", {
            "fields": (
                "created_by",
                "updated_by",
                "created_at",
                "updated_at",
            ),
            "classes": ("tabs",),
        }),
        ("Token", {
            "fields": (
                "input_token",
                "output_token",
                "total_token",
            ),
            "classes": ("tabs",),
        }),
    )

@admin.register(StoryNarrationSettings)
class StoryNarrationSettingsAdmin(ModelAdmin, SingletonModelAdmin):
    """Admin configuration for Story Narration Settings (singleton)."""
    readonly_fields = ["total_token_used"]
    
    fieldsets = (
        (_("Maintenance"), {
            "fields": ("is_maintenance",),
            "description": _("Enable maintenance mode to disable story narration."),
        }),
        (_("Token Configuration"), {
            "fields": ("daily_token_quota", "total_token_used"),
            "description": _("Configure daily token usage limits."),
        }),
        (_("AI Configuration"), {
            "fields": ("ai_model", "voice_type", "background_music", "ai_model_txt"),
            "description": _("Configure the AI model for story narration."),
        }),
    )

        