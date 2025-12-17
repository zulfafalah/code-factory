from django.db import models

class Manhwa(models.Model):
    url = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    download_status = models.CharField(max_length=255, 
        choices=(
            ('pending', 'Pending'), 
            ('completed', 'Completed'), 
            ('failed', 'Failed'),
            ('in progress', 'In Progress')
            ), 
        default='pending')
    content = models.TextField(null=True, blank=True)
    zip_file = models.FileField(upload_to='zip_files/', null=True, blank=True)

    def __str__(self):
        return self.title