from django.db import models


class YouTubeMP3(models.Model):
    DOWNLOAD_STATUS = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    video_url = models.URLField(max_length=200, unique=True)
    download_status = models.CharField(
        max_length=20, choices=DOWNLOAD_STATUS, default="pending"
    )
    video_title = models.CharField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to the downloaded MP3 file",
    )
    file_size = models.PositiveIntegerField(
        blank=True, null=True, help_text="File size in bytes"
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.video_url} - {self.download_status}"

    class Meta:
        verbose_name = "YouTube MP3 Downloader"
        verbose_name_plural = "YouTube MP3 Downloaders"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.video_url.startswith("http"):
            raise ValueError("Invalid URL: Must start with 'http' or 'https'")

        # Check if this is a new instance (not yet saved to database)
        is_new = self.pk is None

        # Save the instance first
        super().save(*args, **kwargs)

        # If this is a new instance and status is pending, automatically start download
        if is_new and self.download_status == "pending":
            try:
                self.start_download()
            except Exception as e:
                # Log the error but don't raise it to prevent save from failing
                self.error_message = f"Failed to start download: {str(e)}"
                self.download_status = "failed"
                # Save again to update the error status
                super().save(update_fields=["error_message", "download_status"])

    def start_download(self):
        """
        Method to start the background download task.
        """
        from .tasks import download_youtube_mp3

        if self.download_status == "pending":
            # Update status immediately
            self.download_status = "in_progress"
            # Use update_fields to avoid triggering save recursion
            super().save(update_fields=["download_status", "updated_at"])

            # Start the Celery task
            task = download_youtube_mp3.delay(self.id)
            return task
        else:
            raise ValueError(
                f"Cannot start download. Current status: {self.download_status}"
            )

    @property
    def file_size_mb(self):
        """
        Returns file size in MB for display purposes.
        """
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    @property
    def is_downloadable(self):
        """
        Check if the file is ready for download.
        """
        from pathlib import Path

        return (
            self.download_status == "completed"
            and self.file_path
            and Path(self.file_path).exists()
        )

    def get_download_url(self):
        """
        Get the URL for downloading the MP3 file.
        """
        if self.is_downloadable:
            from django.urls import reverse

            return reverse("yttoolkit:download_file", kwargs={"download_id": self.id})
        return None
