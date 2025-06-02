from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import YouTubeMP3

# Register your models here.

@admin.register(YouTubeMP3)
class YouTubeMP3Admin(admin.ModelAdmin):
    list_display = [
        'video_url_short',
        'video_title_short',
        'download_status',
        'file_size_display',
        'created_at',
        'updated_at',
        'action_buttons'
    ]
    list_filter = ['download_status', 'created_at']
    search_fields = ['video_url', 'video_title']
    readonly_fields = ['video_title', 'file_name', 'file_size', 'error_message', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('video_url', 'download_status')
        }),
        ('Download Details', {
            'fields': ('video_title', 'file_name', 'file_size', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['start_download_action', 'retry_failed_downloads']

    def video_url_short(self, obj):
        """Display shortened URL for better readability"""
        if len(obj.video_url) > 50:
            return obj.video_url[:47] + '...'
        return obj.video_url
    video_url_short.short_description = 'Video URL'

    def video_title_short(self, obj):
        """Display shortened title for better readability"""
        if obj.video_title:
            if len(obj.video_title) > 40:
                return obj.video_title[:37] + '...'
            return obj.video_title
        return '-'
    video_title_short.short_description = 'Title'

    def file_size_display(self, obj):
        """Display file size in MB"""
        if obj.file_size_mb:
            return f"{obj.file_size_mb} MB"
        return '-'
    file_size_display.short_description = 'File Size'

    def action_buttons(self, obj):
        """Display action buttons for each record"""
        if obj.download_status == 'pending':
            return format_html(
                '<button onclick="startDownload({})" style="background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Start Download</button>',
                obj.id
            )
        elif obj.download_status == 'failed':
            return format_html(
                '<button onclick="retryDownload({})" style="background-color: #ffc107; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Retry</button>',
                obj.id
            )
        return '-'
    action_buttons.short_description = 'Actions'

    def start_download_action(self, request, queryset):
        """Admin action to start downloads for selected items"""
        count = 0
        for youtube_mp3 in queryset:
            if youtube_mp3.download_status == 'pending':
                try:
                    youtube_mp3.start_download()
                    count += 1
                except ValueError:
                    pass

        if count:
            self.message_user(request, f"Started {count} downloads.")
        else:
            self.message_user(request, "No pending downloads found in selection.")
    start_download_action.short_description = "Start download for selected items"

    def retry_failed_downloads(self, request, queryset):
        """Admin action to retry failed downloads"""
        count = 0
        for youtube_mp3 in queryset.filter(download_status='failed'):
            youtube_mp3.download_status = 'pending'
            youtube_mp3.error_message = None
            youtube_mp3.save()
            try:
                youtube_mp3.start_download()
                count += 1
            except ValueError:
                pass

        if count:
            self.message_user(request, f"Retried {count} failed downloads.")
        else:
            self.message_user(request, "No failed downloads found in selection.")
    retry_failed_downloads.short_description = "Retry failed downloads"

    class Media:
        js = ('admin/js/youtube_mp3_admin.js',)
