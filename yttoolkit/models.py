from django.db import models


class YouTubeMP3(models.Model):
    DOWNLOAD_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    video_url = models.URLField(max_length=200, unique=True)
    download_status = models.CharField(max_length=20, choices=DOWNLOAD_STATUS, default='pending')
    video_title = models.CharField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text="File size in bytes")
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.video_url} - {self.download_status}"

    class Meta:
        verbose_name = "YouTube MP3 Downloader"
        verbose_name_plural = "YouTube MP3 Downloaders"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.video_url.startswith('http'):
            raise ValueError("Invalid URL: Must start with 'http' or 'https'")
        super().save(*args, **kwargs)

    def start_download(self):
        """
        Method to start the background download task.
        """
        from .tasks import download_youtube_mp3

        if self.download_status == 'pending':
            # Update status immediately
            self.download_status = 'in_progress'
            self.save()

            # Start the Celery task
            task = download_youtube_mp3.delay(self.id)
            return task
        else:
            raise ValueError(f"Cannot start download. Current status: {self.download_status}")

    @property
    def file_size_mb(self):
        """
        Returns file size in MB for display purposes.
        """
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
