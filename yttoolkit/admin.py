from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import YouTubeMP3

# Register your models here.


@admin.register(YouTubeMP3)
class YouTubeMP3Admin(ModelAdmin):
    # Constants for display text truncation
    URL_DISPLAY_LENGTH = 50
    URL_TRUNCATE_LENGTH = 47
    TITLE_DISPLAY_LENGTH = 40
    TITLE_TRUNCATE_LENGTH = 37

    list_display = [
        "video_url_short",
        "video_title_short",
        "download_status",
        "file_size_display",
        "file_exists_status",
        "download_link",
        "created_at",
    ]
    list_filter = ["download_status", "created_at"]
    search_fields = ["video_url", "video_title"]
    readonly_fields = [
        "video_title",
        "file_name",
        "file_path",
        "file_size",
        "error_message",
        "created_at",
        "updated_at",
        "download_status",
    ]
    list_per_page = 20
    list_select_related = True
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    save_as = True

    fieldsets = (
        ("Basic Information", {"fields": ("video_url", "download_status")}),
        (
            "Download Details",
            {
                "fields": (
                    "video_title",
                    "file_name",
                    "file_path",
                    "file_size",
                    "error_message",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["start_download_action", "retry_failed_downloads"]

    def video_url_short(self, obj):
        """Display shortened URL for better readability"""
        if len(obj.video_url) > self.URL_DISPLAY_LENGTH:
            return obj.video_url[: self.URL_TRUNCATE_LENGTH] + "..."
        return obj.video_url

    video_url_short.short_description = "Video URL"

    def video_title_short(self, obj):
        """Display shortened title for better readability"""
        if obj.video_title:
            if len(obj.video_title) > self.TITLE_DISPLAY_LENGTH:
                return obj.video_title[: self.TITLE_TRUNCATE_LENGTH] + "..."
            return obj.video_title
        return "-"

    video_title_short.short_description = "Title"

    def file_size_display(self, obj):
        """Display file size in MB"""
        if obj.file_size_mb:
            return f"{obj.file_size_mb} MB"
        return "-"

    file_size_display.short_description = "File Size"

    def download_link(self, obj):
        """Display download link for completed files"""
        if obj.is_downloadable:
            try:
                download_url = obj.get_download_url()
                if download_url:
                    return format_html(
                        '<a href="{}" target="_blank" class="button">Download MP3</a>',
                        download_url,
                    )
            except (ImportError, AttributeError, ValueError):
                # If URL generation fails, show error status
                return format_html(
                    '<span style="color: red;">URL Error</span>',
                )
        if obj.download_status == "completed" and obj.file_path:
            return format_html(
                '<span style="color: red;">File not found</span>',
            )
        if obj.download_status == "failed":
            return format_html(
                '<span style="color: orange;">Download failed</span>',
            )
        if obj.download_status == "in_progress":
            return format_html(
                '<span style="color: blue;">Downloading...</span>',
            )
        return format_html(
            '<span style="color: gray;">Not ready</span>',
        )

    download_link.short_description = "Download"
    download_link.allow_tags = True

    def start_download_action(self, request, queryset):
        """Admin action to start download for selected items"""
        started_count = 0
        error_count = 0

        for obj in queryset:
            try:
                if obj.download_status == "pending":
                    obj.start_download()
                    started_count += 1
                elif obj.download_status == "failed":
                    obj.download_status = "pending"
                    obj.error_message = ""
                    obj.save()
                    obj.start_download()
                    started_count += 1
            except ValueError:
                error_count += 1

        if started_count > 0:
            self.message_user(
                request,
                f"Started download for {started_count} items.",
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to start download for {error_count} items.",
                level="ERROR",
            )

    start_download_action.short_description = "Start download for selected items"

    def retry_failed_downloads(self, request, queryset):
        """Admin action to retry failed downloads"""
        failed_items = queryset.filter(download_status="failed")
        retry_count = 0

        for obj in failed_items:
            try:
                obj.download_status = "pending"
                obj.error_message = ""
                obj.save()
                obj.start_download()
                retry_count += 1
            except ValueError:
                # Log the error but continue with other items
                continue

        if retry_count > 0:
            self.message_user(
                request,
                f"Retrying download for {retry_count} failed items.",
            )
        else:
            self.message_user(
                request,
                "No failed downloads found in selection.",
                level="WARNING",
            )

    retry_failed_downloads.short_description = "Retry failed downloads"

    def file_path_display(self, obj):
        """Display file path with proper formatting"""
        if obj.file_path:
            # Show only the filename for better readability
            from pathlib import Path

            return Path(obj.file_path).name
        return "-"

    file_path_display.short_description = "File Name"

    def file_exists_status(self, obj):
        """Check if the downloaded file exists"""
        if obj.file_path:
            from pathlib import Path

            if Path(obj.file_path).exists():
                return format_html(
                    '<span style="color: green;">✓ Exists</span>',
                )
            return format_html(
                '<span style="color: red;">✗ Missing</span>',
            )
        return "-"

    file_exists_status.short_description = "File Status"
