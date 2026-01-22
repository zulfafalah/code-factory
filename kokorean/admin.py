from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Manhwa


@admin.register(Manhwa)
class ManhwaAdmin(ModelAdmin):
    list_display = ["title", "url", "download_status", "created_at", "updated_at"]
    list_filter = ["download_status"]
    search_fields = ["title", "url"]
    ordering = ["-created_at"]