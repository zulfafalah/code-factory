from django.contrib import admin
from .models import StoryNarration
from unfold.admin import ModelAdmin

# Register your models here.

@admin.register(StoryNarration)
class StoryNarrationAdmin(ModelAdmin):
    list_display = ["title", "status", "created_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by", "status", "input_token", "output_token", "total_token", "result_file"]  

    def save_model(self, request, obj, form, change):   
        if not change:  # Creating a new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    fieldsets = (
        ("General", {
            "fields": (
                "title",
                "content_text",
                "source_url",
                "final_content",
                "status",
                "result_file",
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
        