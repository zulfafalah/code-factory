#!/usr/bin/env python3
"""
Example script demonstrating how to use the YouTube MP3 downloader API.
This script shows both the Django management command and the API endpoints.
"""

import requests
import time
import json


def test_api_download(base_url, video_url):
    """Test the API endpoint for starting downloads"""
    print(f"🚀 Testing API download for: {video_url}")

    # Start download via API
    start_url = f"{base_url}/yttoolkit/api/start/"
    payload = {"video_url": video_url}

    try:
        response = requests.post(
            start_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Download started successfully!")
                print(f"   Task ID: {data['task_id']}")
                print(f"   Download ID: {data['download_id']}")

                # Monitor download status
                download_id = data['download_id']
                monitor_download_status(base_url, download_id)
            else:
                print(f"⚠️  {data['message']}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")


def monitor_download_status(base_url, download_id):
    """Monitor download status via API"""
    status_url = f"{base_url}/yttoolkit/api/status/{download_id}/"

    print("\n📊 Monitoring download status...")

    for i in range(30):  # Monitor for up to 5 minutes (30 * 10 seconds)
        try:
            response = requests.get(status_url)

            if response.status_code == 200:
                data = response.json()
                status = data['download_status']

                print(f"   Status: {status}")

                if data['video_title']:
                    print(f"   Title: {data['video_title']}")

                if status == 'completed':
                    print(f"🎉 Download completed!")
                    if data['file_size_mb']:
                        print(f"   File size: {data['file_size_mb']} MB")
                    if data['file_name']:
                        print(f"   File name: {data['file_name']}")
                    break
                elif status == 'failed':
                    print(f"❌ Download failed!")
                    if data['error_message']:
                        print(f"   Error: {data['error_message']}")
                    break
                elif status == 'in_progress':
                    print("   Download in progress...")

                time.sleep(10)  # Wait 10 seconds before next check
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
            break
    else:
        print("⏱️  Monitoring timeout reached")


def main():
    """Main function to demonstrate the YouTube MP3 downloader"""
    print("🎵 YouTube MP3 Downloader - Example Usage")
    print("=" * 50)

    # Configuration
    base_url = "http://localhost:8000"  # Adjust if your Django app runs on different port
    test_video_url = "https://www.youtube.com/watch?v=IEw7jsWH5Us&ab_channel=%F0%9D%99%AC%F0%9D%99%A8%F0%9D%99%AB%F0%9D%99%9E%F0%9D%99%97%F0%9D%99%9A%F0%9D%99%A8%F0%9D%99%A8"

    print("\n1. Using Django Management Command:")
    print("-" * 40)
    print("   # Start download in background:")
    print(f"   python manage.py download_youtube_mp3 '{test_video_url}'")
    print("")
    print("   # Start download synchronously (for testing):")
    print(f"   python manage.py download_youtube_mp3 '{test_video_url}' --sync")

    print("\n2. Using Celery Tasks Directly:")
    print("-" * 40)
    print("   # In Django shell or Python script:")
    print("   from yttoolkit.models import YouTubeMP3")
    print("   from yttoolkit.tasks import download_youtube_mp3")
    print("")
    print("   # Create model instance")
    print(f"   youtube_mp3 = YouTubeMP3.objects.create(video_url='{test_video_url}')")
    print("")
    print("   # Start download using model method")
    print("   task = youtube_mp3.start_download()")
    print("   print(f'Task ID: {task.id}')")
    print("")
    print("   # Or call task directly")
    print("   task = download_youtube_mp3.delay(youtube_mp3.id)")

    print("\n3. Using REST API:")
    print("-" * 40)

    # Test the API if user confirms
    try:
        user_input = input("\nWould you like to test the API endpoint? (y/n): ").lower().strip()
        if user_input == 'y':
            test_api_download(base_url, test_video_url)
        else:
            print("Skipping API test.")
    except KeyboardInterrupt:
        print("\nSkipping API test.")

    print("\n4. Monitoring with Celery:")
    print("-" * 40)
    print("   # Check Celery worker status:")
    print("   celery -A config.celery_app inspect ping")
    print("")
    print("   # Monitor tasks:")
    print("   celery -A config.celery_app events")
    print("")
    print("   # Flower web interface (if running):")
    print("   http://localhost:5555")

    print("\n5. Docker Commands:")
    print("-" * 40)
    print("   # Start all services:")
    print("   docker compose -f docker-compose.local.yml up")
