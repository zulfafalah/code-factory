#!/usr/bin/env python
"""
Simple test script to test the YouTube MP3 download functionality
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from yttoolkit.models import YouTubeMP3


def test_download():
    # Use a short test video URL (replace with actual YouTube URL)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video

    print(f"Creating download for: {test_url}")

    # Create a new download
    youtube_mp3, created = YouTubeMP3.objects.get_or_create(
        video_url=test_url, defaults={"download_status": "pending"}
    )

    if created:
        print(f"✅ Created new download with ID: {youtube_mp3.id}")
        print(f"📊 Status: {youtube_mp3.download_status}")
        print("🚀 Download will start automatically in background...")
    else:
        print(f"📋 Download already exists with ID: {youtube_mp3.id}")
        print(f"📊 Current status: {youtube_mp3.download_status}")

        if youtube_mp3.is_downloadable:
            print(f"✅ File is ready for download!")
            print(f"📁 File path: {youtube_mp3.file_path}")
            print(f"🔗 Download URL: {youtube_mp3.get_download_url()}")
        elif youtube_mp3.download_status == "failed":
            print(f"❌ Download failed: {youtube_mp3.error_message}")
        else:
            print("⏳ Download is still in progress...")

    return youtube_mp3


if __name__ == "__main__":
    test_download()
