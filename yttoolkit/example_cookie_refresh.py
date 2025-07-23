#!/usr/bin/env python3
"""
Example script showing how to use the cookie refresh functionality.

This script demonstrates different ways to refresh YouTube cookies:
1. Using the Django management command
2. Using the Celery task directly
3. Using the API endpoint
4. Using the refresh_cookie module directly

Usage:
    python example_cookie_refresh.py
"""

import os
import sys
import requests
import json

# Add the project directory to Python path
sys.path.append('/home/fallah/Development/Labs/palpal')

def example_management_command():
    """Example using Django management command"""
    print("=== Example 1: Using Django Management Command ===")

    commands = [
        # Test existing cookies
        "python manage.py refresh_cookies --test-only",

        # Refresh cookies synchronously with Chrome
        "python manage.py refresh_cookies --sync",

        # Refresh cookies with Chromium browser
        "python manage.py refresh_cookies --chromium",

        # Refresh cookies with custom cookie file
        "python manage.py refresh_cookies --cookie-file /tmp/my_cookies.txt --sync",

        # Run async with Celery (default)
        "python manage.py refresh_cookies"
    ]

    print("Available management commands:")
    for cmd in commands:
        print(f"  {cmd}")

    print("\nExample usage:")
    print("  cd /home/fallah/Development/Labs/palpal")
    print("  python manage.py refresh_cookies --sync")


def example_celery_task():
    """Example using Celery task directly"""
    print("\n=== Example 2: Using Celery Task Directly ===")

    try:
        # This would require Django setup
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

        import django
        django.setup()

        from yttoolkit.tasks import refresh_youtube_cookies, scheduled_cookie_refresh

        print("Starting cookie refresh task...")

        # Method 1: Direct task call
        result = refresh_youtube_cookies.delay(
            cookie_file_path="/tmp/cookies.txt",
            use_chromium=False
        )

        print(f"Task started with ID: {result.id}")

        # Wait for result (optional)
        # task_result = result.get(timeout=300)
        # print(f"Task result: {task_result}")

        # Method 2: Scheduled task
        scheduled_result = scheduled_cookie_refresh.delay(
            cookie_file_path="/tmp/cookies.txt",
            use_chromium=True
        )

        print(f"Scheduled task ID: {scheduled_result.id}")

    except Exception as e:
        print(f"Error: {e}")
        print("Note: This requires Django setup and Celery worker running")


def example_api_endpoint():
    """Example using API endpoint"""
    print("\n=== Example 3: Using API Endpoint ===")

    # Assuming the server is running on localhost:8000
    base_url = "http://localhost:8000/api/yttoolkit/cookies"

    # Example 1: Get cookie status
    print("1. Getting cookie status...")
    try:
        response = requests.get(f"{base_url}/refresh/")
        print(f"Status response: {response.json()}")
    except Exception as e:
        print(f"Error getting status: {e}")

    # Example 2: Test existing cookies only
    print("\n2. Testing existing cookies...")
    try:
        test_data = {
            "test_only": True,
            "cookie_file": "/tmp/cookies.txt"
        }
        response = requests.post(f"{base_url}/refresh/", json=test_data)
        print(f"Test response: {response.json()}")
    except Exception as e:
        print(f"Error testing cookies: {e}")

    # Example 3: Refresh cookies synchronously
    print("\n3. Refreshing cookies synchronously...")
    try:
        refresh_data = {
            "sync": True,
            "use_chromium": False,
            "cookie_file": "/tmp/cookies.txt"
        }
        response = requests.post(f"{base_url}/refresh/", json=refresh_data)
        print(f"Sync refresh response: {response.json()}")
    except Exception as e:
        print(f"Error refreshing cookies sync: {e}")

    # Example 4: Refresh cookies asynchronously
    print("\n4. Refreshing cookies asynchronously...")
    try:
        async_data = {
            "sync": False,
            "use_chromium": True,
            "cookie_file": "/tmp/cookies.txt"
        }
        response = requests.post(f"{base_url}/refresh/", json=async_data)
        result = response.json()
        print(f"Async refresh response: {result}")

        if result.get('success') and result.get('task_id'):
            print(f"Task scheduled with ID: {result['task_id']}")
            print("You can check task status using Celery monitoring tools")
    except Exception as e:
        print(f"Error refreshing cookies async: {e}")


def example_direct_usage():
    """Example using refresh_cookie module directly"""
    print("\n=== Example 4: Using refresh_cookie Module Directly ===")

    try:
        # Import the refresh_cookie functions
        sys.path.append('/home/fallah/Development/Labs/palpal/yttoolkit')
        from refresh_cookie import (
            update_cookies,
            test_cookies,
            test_authenticated_access,
            clean_expired_cookies
        )

        cookie_file = "/tmp/cookies.txt"

        print(f"Using cookie file: {cookie_file}")

        # 1. Clean expired cookies
        print("1. Cleaning expired cookies...")
        clean_result = clean_expired_cookies(cookie_file)
        print(f"Clean result: {clean_result}")

        # 2. Test existing cookies
        print("\n2. Testing existing cookies...")
        test_result = test_cookies(cookie_file)
        print(f"Basic test result: {test_result}")

        auth_result = test_authenticated_access(cookie_file)
        print(f"Auth test result: {auth_result}")

        # 3. Refresh cookies if needed
        if not test_result or not auth_result:
            print("\n3. Refreshing cookies...")
            refresh_result = update_cookies(cookie_file, use_chromium=False)
            print(f"Refresh result: {refresh_result}")

            if refresh_result:
                # Test again
                print("\n4. Testing refreshed cookies...")
                new_test_result = test_cookies(cookie_file)
                new_auth_result = test_authenticated_access(cookie_file)
                print(f"New test results: basic={new_test_result}, auth={new_auth_result}")
        else:
            print("Cookies are working fine, no refresh needed!")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure the refresh_cookie.py module is accessible")
    except Exception as e:
        print(f"Error: {e}")


def example_scheduled_refresh():
    """Example of setting up scheduled cookie refresh"""
    print("\n=== Example 5: Scheduled Cookie Refresh ===")

    print("To set up automatic cookie refresh, add this to your Celery Beat schedule:")
    print("""
# In your Django settings (e.g., config/settings/local.py):

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'refresh-youtube-cookies': {
        'task': 'yttoolkit.tasks.scheduled_cookie_refresh',
        'schedule': crontab(hour=6, minute=0),  # Run daily at 6:00 AM
        'args': ('/tmp/cookies.txt', False),  # (cookie_file, use_chromium)
    },
}

# Start Celery Beat:
# celery -A config.celery_app beat --loglevel=info
""")

    print("\nAlternatively, you can trigger it manually:")
    print("""
# In Django shell or script:
from yttoolkit.tasks import scheduled_cookie_refresh
result = scheduled_cookie_refresh.delay('/tmp/cookies.txt', False)
print(f"Scheduled task ID: {result.id}")
""")


if __name__ == "__main__":
    print("YouTube Cookie Refresh Examples")
    print("=" * 50)

    # Show all examples
    example_management_command()
    example_celery_task()
    example_api_endpoint()
    example_direct_usage()
    example_scheduled_refresh()

    print("\n" + "=" * 50)
    print("Cookie Refresh Setup Complete!")
    print("\nNext steps:")
    print("1. Make sure Celery worker is running:")
    print("   celery -A config.celery_app worker --loglevel=info")
    print("\n2. Make sure your cookies.txt file exists:")
    print("   # Export from browser and place at /tmp/cookies.txt")
    print("\n3. Test the functionality:")
    print("   python manage.py refresh_cookies --test-only")
    print("\n4. For production, set up Celery Beat for automatic refresh:")
    print("   celery -A config.celery_app beat --loglevel=info")
