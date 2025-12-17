from django.contrib import admin
from .models import Manhwa
# Register your models here.

@admin.register(Manhwa)
class ManhwaAdmin(admin.ModelAdmin):
    list_display = ('url', 'title', 'created_at', 'updated_at', 'download_status')