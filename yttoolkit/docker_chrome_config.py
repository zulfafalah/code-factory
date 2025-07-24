#!/usr/bin/env python3
"""
Docker-optimized Chrome configuration for Selenium WebDriver
Use this configuration in your refresh_cookie.py or other Selenium scripts
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

def get_docker_chrome_options(headless=True):
    """
    Get Chrome options optimized for Docker containers
    """
    chrome_options = Options()

    # Essential options for Docker
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--window-size=1920,1080")

    # Memory optimization
    chrome_options.add_argument("--max_old_space_size=4096")
    chrome_options.add_argument("--memory-pressure-off")

    # Security options
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    # Headless mode
    if headless:
        chrome_options.add_argument("--headless=new")  # Use new headless mode

    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Set binary location if specified in environment
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome')
    if os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin

    return chrome_options

def create_docker_webdriver(headless=True):
    """
    Create a WebDriver instance optimized for Docker
    """
    chrome_options = get_docker_chrome_options(headless)

    try:
        # Install and use ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set timeouts
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)

        return driver

    except Exception as e:
        print(f"Error creating Docker WebDriver: {str(e)}")
        raise

# Example usage
if __name__ == "__main__":
    print("Testing Docker Chrome WebDriver...")

    try:
        driver = create_docker_webdriver(headless=True)
        driver.get("https://www.google.com")
        print(f"✅ Successfully loaded Google! Title: {driver.title}")
        driver.quit()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
