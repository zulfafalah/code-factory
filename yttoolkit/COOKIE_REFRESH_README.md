# YouTube Cookie Refresh - Background Task Implementation

This implementation provides several ways to refresh YouTube cookies for authentication in the background using Celery.

## Features

✅ **Celery Background Task** - Refresh cookies without blocking the main application
✅ **Django Management Command** - Easy command-line interface 
✅ **REST API Endpoint** - HTTP API for web applications
✅ **Sync/Async Modes** - Choose between immediate or background execution
✅ **Cookie Testing** - Validate cookies without refreshing
✅ **Browser Support** - Works with both Chrome and Chromium
✅ **Error Handling** - Comprehensive error handling and retry logic
✅ **Scheduling Support** - Can be scheduled with Celery Beat

## Quick Start

### 1. Start Celery Worker
```bash
cd /home/fallah/Development/Labs/palpal
celery -A config.celery_app worker --loglevel=info
```

### 2. Test Cookie Refresh
```bash
# Test existing cookies
python manage.py refresh_cookies --test-only

# Refresh cookies synchronously  
python manage.py refresh_cookies --sync

# Refresh cookies in background (default)
python manage.py refresh_cookies
```

## Usage Methods

### 1. Django Management Command

```bash
# Basic usage
python manage.py refresh_cookies

# With custom cookie file
python manage.py refresh_cookies --cookie-file /path/to/cookies.txt

# Use Chromium browser
python manage.py refresh_cookies --chromium

# Run synchronously (no Celery)
python manage.py refresh_cookies --sync

# Test only (no refresh)
python manage.py refresh_cookies --test-only
```

### 2. Celery Task (Python Code)

```python
from yttoolkit.tasks import refresh_youtube_cookies

# Schedule background task
result = refresh_youtube_cookies.delay(
    cookie_file_path="/tmp/cookies.txt",
    use_chromium=False
)

print(f"Task ID: {result.id}")

# Wait for result (optional)
task_result = result.get(timeout=300)
print(f"Result: {task_result}")
```

### 3. REST API Endpoint

**Base URL:** `/api/yttoolkit/cookies/refresh/`

#### GET - Get Cookie Status
```bash
curl -X GET "http://localhost:8000/api/yttoolkit/cookies/refresh/"
```

#### POST - Refresh Cookies
```bash
# Async refresh (background task)
curl -X POST "http://localhost:8000/api/yttoolkit/cookies/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "cookie_file": "/tmp/cookies.txt",
    "use_chromium": false,
    "sync": false
  }'

# Sync refresh (immediate)
curl -X POST "http://localhost:8000/api/yttoolkit/cookies/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "cookie_file": "/tmp/cookies.txt", 
    "use_chromium": false,
    "sync": true
  }'

# Test only
curl -X POST "http://localhost:8000/api/yttoolkit/cookies/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "cookie_file": "/tmp/cookies.txt",
    "test_only": true
  }'
```

### 4. Direct Module Usage

```python
from yttoolkit.refresh_cookie import (
    update_cookies, 
    test_cookies, 
    test_authenticated_access, 
    clean_expired_cookies
)

cookie_file = "/tmp/cookies.txt"

# Clean expired cookies
clean_expired_cookies(cookie_file)

# Test existing cookies
basic_test = test_cookies(cookie_file)
auth_test = test_authenticated_access(cookie_file)

# Refresh if needed
if not basic_test or not auth_test:
    update_cookies(cookie_file, use_chromium=False)
```

## Scheduled Refresh

Set up automatic cookie refresh using Celery Beat:

### 1. Add to Django Settings

```python
# config/settings/base.py or local.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'refresh-youtube-cookies': {
        'task': 'yttoolkit.tasks.scheduled_cookie_refresh',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6:00 AM
        'args': ('/tmp/cookies.txt', False),    # (cookie_file, use_chromium)
    },
}

# Optional: Set default cookie file path
YOUTUBE_COOKIES_PATH = '/tmp/cookies.txt'
```

### 2. Start Celery Beat

```bash
celery -A config.celery_app beat --loglevel=info
```

## Task Functions

### `refresh_youtube_cookies(cookie_file_path, use_chromium)`
Main Celery task for refreshing cookies.

**Parameters:**
- `cookie_file_path` (str): Path to cookies.txt file
- `use_chromium` (bool): Use Chromium instead of Chrome

**Returns:** Dict with status, message, and test results

### `scheduled_cookie_refresh(cookie_file_path, use_chromium)`
Wrapper task for scheduled execution.

**Parameters:** Same as above
**Returns:** Dict with task scheduling information

## API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Cookies refreshed successfully!",
  "task_id": "abc123...",
  "cookie_file": "/tmp/cookies.txt",
  "test_passed": true,
  "auth_test_passed": true,
  "browser_used": "chrome"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Cookie refresh failed: Browser not found"
}
```

## Configuration

### Environment Variables
```bash
# Optional: Set cookies via environment variable
export YOUTUBE_COOKIES_JSON='[{"name":"SESSION_TOKEN","value":"abc123",...}]'

# Optional: Set default cookie file path
export YOUTUBE_COOKIES_PATH="/custom/path/cookies.txt"
```

### Django Settings
```python
# Custom cookie file path
YOUTUBE_COOKIES_PATH = '/custom/path/cookies.txt'

# Celery configuration for cookie tasks
CELERY_TASK_ROUTES = {
    'yttoolkit.tasks.refresh_youtube_cookies': {'queue': 'cookies'},
    'yttoolkit.tasks.scheduled_cookie_refresh': {'queue': 'cookies'},
}
```

## Troubleshooting

### Common Issues

1. **Browser not found**
   ```bash
   # Install Chrome/Chromium
   sudo apt update
   sudo apt install chromium-browser
   # or
   sudo apt install google-chrome-stable
   ```

2. **Selenium WebDriver issues**
   ```bash
   # Install webdriver-manager
   pip install webdriver-manager
   ```

3. **Celery worker not running**
   ```bash
   # Start Celery worker
   celery -A config.celery_app worker --loglevel=info
   ```

4. **Cookie file permissions**
   ```bash
   # Fix permissions
   chmod 644 /tmp/cookies.txt
   chown $USER:$USER /tmp/cookies.txt
   ```

### Monitoring

```bash
# Check Celery worker status
celery -A config.celery_app status

# Monitor tasks
celery -A config.celery_app events

# Check task result
from celery.result import AsyncResult
result = AsyncResult('task-id-here')
print(result.status)
print(result.result)
```

## Files Created

1. **`tasks.py`** - Added Celery tasks for cookie refresh
2. **`management/commands/refresh_cookies.py`** - Django management command
3. **`views.py`** - Added REST API endpoint for cookie refresh
4. **`urls.py`** - Added URL routing for API endpoint
5. **`example_cookie_refresh.py`** - Usage examples and documentation

## Testing

```python
# Test the cookie refresh functionality
python yttoolkit/example_cookie_refresh.py

# Or use the management command
python manage.py refresh_cookies --test-only
```

## Next Steps

1. **Set up your cookies.txt file** - Export from browser
2. **Start Celery worker** - `celery -A config.celery_app worker`
3. **Test the functionality** - `python manage.py refresh_cookies --test-only`
4. **Set up scheduled refresh** - Add to Celery Beat schedule
5. **Monitor and maintain** - Use Celery monitoring tools

---

**Note:** This implementation works with the existing `refresh_cookie.py` module and extends it with Celery background task capabilities.
