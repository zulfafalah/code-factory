#!/usr/bin/env python3
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def detect_browser():
    """Detect available browser and return appropriate configuration"""
    browsers = {
        'chromium': [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser", 
            "/snap/bin/chromium",
            "/usr/bin/chromium-browser",
            "/opt/chromium/chrome"
        ],
        'chrome': [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/google/chrome/chrome",
            "/usr/bin/chrome"
        ]
    }
    
    for browser_name, paths in browsers.items():
        for path in paths:
            if os.path.exists(path):
                return browser_name, path
    
    return None, None

def get_webdriver(use_chromium=False, headless=True):
    """Get appropriate webdriver based on available browsers"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    if use_chromium:
        browser_name, browser_path = detect_browser()
        if browser_name == 'chromium' and browser_path:
            chrome_options.binary_location = browser_path
            print(f"Using Chromium binary: {browser_path}")
        elif browser_name == 'chrome' and browser_path:
            chrome_options.binary_location = browser_path
            print(f"Using Chrome binary: {browser_path}")
        else:
            print("Warning: No Chromium/Chrome binary found, using default")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error creating webdriver: {str(e)}")
        raise

def load_existing_cookies(driver, cookie_file_path):
    """Load existing cookies from cookies.txt file"""
    if not os.path.exists(cookie_file_path):
        print(f"Cookie file {cookie_file_path} not found!")
        return False
    
    try:
        with open(cookie_file_path, 'r') as f:
            lines = f.readlines()
        
        # Navigate to YouTube first to set domain
        driver.get("https://www.youtube.com")
        time.sleep(2)
        
        cookies_loaded = 0
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue
            
            try:
                # Parse Netscape cookie format
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain = parts[0]
                    path = parts[2]
                    secure = parts[3] == 'TRUE'
                    expiry = parts[4]
                    name = parts[5]
                    value = parts[6]
                    
                    # Only add YouTube related cookies
                    if 'youtube.com' in domain or 'google.com' in domain:
                        cookie_dict = {
                            'name': name,
                            'value': value,
                            'domain': domain,
                            'path': path,
                            'secure': secure
                        }
                        
                        # Add expiry if it's not 0
                        if expiry != '0' and expiry.isdigit():
                            cookie_dict['expiry'] = int(expiry)
                        
                        driver.add_cookie(cookie_dict)
                        cookies_loaded += 1
                        
            except Exception as e:
                print(f"Error loading cookie: {line[:50]}... - {str(e)}")
                continue
        
        print(f"Loaded {cookies_loaded} cookies from existing file")
        return cookies_loaded > 0
        
    except Exception as e:
        print(f"Error reading cookie file: {str(e)}")
        return False

def save_cookies_to_file(driver, cookie_file_path):
    """Save current cookies to file in Netscape format"""
    try:
        cookies = driver.get_cookies()
        
        # Backup existing file
        if os.path.exists(cookie_file_path):
            backup_path = f"{cookie_file_path}.backup"
            os.rename(cookie_file_path, backup_path)
            print(f"Backup created: {backup_path}")
        
        with open(cookie_file_path, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# Generated by refresh_cookies.py\n")
            f.write("# This file contains the HTTP cookies for YouTube authentication\n\n")
            
            cookies_saved = 0
            for cookie in cookies:
                domain = cookie.get('domain', '')
                path = cookie.get('path', '/')
                secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                expiry = str(cookie.get('expiry', '0'))
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                
                # Only save YouTube and Google related cookies
                if any(x in domain for x in ['youtube.com', 'google.com', 'googleapis.com', 'gstatic.com']):
                    f.write(f"{domain}\tTRUE\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
                    cookies_saved += 1
            
        print(f"Saved {cookies_saved} cookies to {cookie_file_path}")
        return True
        
    except Exception as e:
        print(f"Error saving cookies: {str(e)}")
        return False

def update_cookies(cookie_file_path="/root/cookies.txt", use_chromium=False):
    """Main function to refresh cookies"""
    print("Starting cookie refresh process...")
    
    # Start browser
    try:
        driver = get_webdriver(use_chromium=use_chromium)
        
        # Load existing cookies first
        print(f"Loading existing cookies from {cookie_file_path}...")
        cookies_loaded = load_existing_cookies(driver, cookie_file_path)
        
        if cookies_loaded:
            print("Refreshing session with existing cookies...")
            # Refresh the page to activate cookies
            driver.refresh()
            time.sleep(5)
            
            # Navigate to some YouTube pages to refresh cookies
            refresh_urls = [
                "https://www.youtube.com",
                "https://www.youtube.com/feed/subscriptions",
                "https://www.youtube.com/feed/library"
            ]
            
            for url in refresh_urls:
                try:
                    print(f"Refreshing: {url}")
                    driver.get(url)
                    time.sleep(3)
                except Exception as e:
                    print(f"Error accessing {url}: {str(e)}")
                    continue
        else:
            print("No existing cookies found or failed to load. Visiting YouTube...")
            driver.get("https://www.youtube.com")
            time.sleep(5)
        
        # Save refreshed cookies
        print("Saving refreshed cookies...")
        if save_cookies_to_file(driver, cookie_file_path):
            print("Cookies refreshed successfully!")
        else:
            print("Failed to save cookies!")
            
    except Exception as e:
        print(f"Error during cookie refresh: {str(e)}")
        return False
        
    finally:
        try:
            driver.quit()
        except:
            pass
    
    return True

def test_cookies(cookie_file_path="/root/cookies.txt"):
    """Test if cookies are working with yt-dlp"""
    print("Testing cookies with yt-dlp...")
    
    # Multiple test URLs to try
    test_urls = [
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Simple test video
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
        "https://www.youtube.com/watch?v=9bZkp7q19f0"   # Gangnam Style
    ]
    
    import subprocess
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"Trying test video {i}/{len(test_urls)}...")
        
        try:
            # First try with basic options
            result = subprocess.run([
                'yt-dlp', 
                '--cookies', cookie_file_path,
                '--simulate',
                '--get-title',
                '--no-warnings',
                '--extractor-args', 'youtube:player_client=web,mweb',
                test_url
            ], capture_output=True, text=True, timeout=45)
            
            if result.returncode == 0 and result.stdout.strip():
                print("✅ Cookies are working! Test video title:", result.stdout.strip())
                return True
            elif result.returncode != 0:
                print(f"❌ Test {i} failed:", result.stderr.strip())
            else:
                print(f"❌ Test {i}: No output received")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Test {i} timed out")
        except Exception as e:
            print(f"❌ Error in test {i}: {str(e)}")
    
    # If all tests fail, try a simple authentication check
    print("All video tests failed. Trying authentication check...")
    try:
        result = subprocess.run([
            'yt-dlp', 
            '--cookies', cookie_file_path,
            '--simulate',
            '--get-url',
            '--playlist-end', '1',
            'https://www.youtube.com/feed/subscriptions'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Authentication check passed - cookies appear to be valid")
            return True
        else:
            print("❌ Authentication check failed:", result.stderr.strip())
            return False
            
    except Exception as e:
        print(f"❌ Error in authentication check: {str(e)}")
        return False

def test_authenticated_access(cookie_file_path="/root/cookies.txt"):
    """Test if cookies can access authenticated content"""
    print("\nTesting authenticated access...")
    
    import subprocess
    
    # Test accessing subscription feed (requires login)
    try:
        result = subprocess.run([
            'yt-dlp', 
            '--cookies', cookie_file_path,
            '--simulate',
            '--flat-playlist',
            '--playlist-end', '5',
            'https://www.youtube.com/feed/subscriptions'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            video_count = len([line for line in lines if line.strip()])
            print(f"✅ Authenticated access working! Found {video_count} videos in subscriptions")
            return True
        else:
            print("❌ Could not access subscription feed")
            if result.stderr:
                print("Error:", result.stderr.strip())
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Authenticated access test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing authenticated access: {str(e)}")
        return False

def clean_expired_cookies(cookie_file_path):
    """Remove expired cookies from cookies.txt file"""
    if not os.path.exists(cookie_file_path):
        return False
    
    import time
    current_time = int(time.time())
    
    try:
        with open(cookie_file_path, 'r') as f:
            lines = f.readlines()
        
        cleaned_lines = []
        removed_count = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Keep comments and empty lines
            if line_stripped.startswith('#') or not line_stripped:
                cleaned_lines.append(line)
                continue
            
            try:
                parts = line_stripped.split('\t')
                if len(parts) >= 7:
                    expiry = parts[4]
                    
                    # If expiry is 0 or not a number, keep the cookie (session cookie)
                    if expiry == '0' or not expiry.isdigit():
                        cleaned_lines.append(line)
                    elif int(expiry) > current_time:
                        # Cookie is still valid
                        cleaned_lines.append(line)
                    else:
                        # Cookie is expired
                        removed_count += 1
                        print(f"Removing expired cookie: {parts[5]}")
                else:
                    # Invalid format, keep as is
                    cleaned_lines.append(line)
                    
            except Exception as e:
                # If there's any error parsing, keep the line
                cleaned_lines.append(line)
                print(f"Warning: Could not parse cookie line: {line_stripped[:50]}...")
        
        # Write back the cleaned cookies
        with open(cookie_file_path, 'w') as f:
            f.writelines(cleaned_lines)
        
        print(f"Cleaned {removed_count} expired cookies")
        return True
        
    except Exception as e:
        print(f"Error cleaning cookies: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Get cookie file path from command line or use default
    cookie_file = sys.argv[1] if len(sys.argv) > 1 else "/root/cookies.txt"
    use_chromium = "--chromium" in sys.argv or "-c" in sys.argv
    
    print(f"Using cookie file: {cookie_file}")
    if use_chromium:
        print("Using Chromium browser")
    
    # Check if cookie file exists
    if not os.path.exists(cookie_file):
        print(f"❌ Cookie file {cookie_file} not found!")
        print("Please upload your cookies.txt file first")
        sys.exit(1)
    
    # Clean expired cookies first
    print("Cleaning expired cookies...")
    clean_expired_cookies(cookie_file)
    
    # Refresh cookies
    if update_cookies(cookie_file, use_chromium):
        # Test the refreshed cookies
        test_cookies(cookie_file)
        test_authenticated_access(cookie_file)
    else:
        print("❌ Cookie refresh failed!")
        sys.exit(1)
    
    # Clean expired cookies
    clean_expired_cookies(cookie_file)

# Usage examples:
# python refresh_cookie.py                    # Use Chrome with default cookies.txt
# python refresh_cookie.py --chromium         # Use Chromium browser
# python refresh_cookie.py cookies.txt -c     # Use Chromium with custom cookie file
# python refresh_cookie.py /path/cookies.txt  # Use Chrome with custom cookie file
