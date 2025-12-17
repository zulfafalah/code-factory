import requests
from bs4 import BeautifulSoup
import json


def fetch_data(url):
    """
    Fetch HTML content from a given URL
    
    Args:
        url (str): URL to fetch data from
        
    Returns:
        str: HTML content or None if error occurs
    """
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def extract_data(html_content):
    """
    Extract title and image URLs from HTML content
    
    Args:
        html_content (str): HTML content to parse
        
    Returns:
        dict: Dictionary containing 'title' and 'image_urls'
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    soup.prettify()
    
    # Extract title
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
    else:
        title_text = "Untitled"
    
    # Extract image URLs
    imgs = soup.select("#toon_content_imgs img")
    image_urls = [img.get("o_src") for img in imgs if img.get("o_src")]
    
    return {
        'title': title_text,
        'image_urls': image_urls
    }


def extract_image_urls_from_url(url):
    """
    Complete process to fetch and extract title and image URLs from a URL
    
    Args:
        url (str): URL to extract data from
        
    Returns:
        dict: Dictionary containing 'success' status, 'title', and either 'image_urls' or 'error' message
    """
    html_content = fetch_data(url)
    
    if html_content is None:
        return {
            'success': False,
            'error': 'Failed to fetch data from URL'
        }
    
    extracted_data = extract_data(html_content)
    
    if not extracted_data['image_urls']:
        return {
            'success': False,
            'error': 'No images found in the content',
            'title': extracted_data.get('title', 'Untitled')
        }
    
    return {
        'success': True,
        'title': extracted_data['title'],
        'image_urls': extracted_data['image_urls']
    }


# Image download and compression functions
# ==========================================

import zipfile
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def download_image(image_url, file_path, timeout=30, max_retries=3):
    """
    Download a single image with retry logic
    
    Args:
        image_url (str): URL of the image to download
        file_path (str): Path to save the image
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        bool: True if successful, False otherwise
    """
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        response = session.get(image_url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        return True
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.RequestException as e:
        return False


def download_image_safe(image_url, filename, timeout=(10, 60)):
    """
    Download image directly to memory without writing to disk
    
    Args:
        image_url (str): Full URL of the image
        filename (str): Filename to use in the zip
        timeout (tuple): Connection and read timeout
        
    Returns:
        tuple: (success:bool, data:dict or error:str)
    """
    try:
        response = requests.get(
            image_url, 
            stream=True, 
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response.raise_for_status()
        
        # Save data to memory
        image_data = b''
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                image_data += chunk
        
        return True, {'filename': filename, 'data': image_data}
    except Exception as e:
        return False, f"{filename}: {str(e)}"


def download_all_parallel(image_urls, base_url, max_workers=3):
    """
    Download images in parallel with limited workers
    
    Args:
        image_urls (list): List of image URLs (relative paths)
        base_url (str): Base URL to prepend to image URLs
        max_workers (int): Number of parallel download threads
        
    Returns:
        dict: Dictionary with 'success' and 'failed' lists
    """
    results = {'success': [], 'failed': []}
    
    def download_task(idx, img_url):
        file_path = f"image_{idx + 1}.jpg"
        image_full_url = base_url + img_url
        return idx, download_image_safe(image_full_url, file_path)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_task, idx, url): idx 
                   for idx, url in enumerate(image_urls)}
        
        for future in as_completed(futures):
            idx, (success, info) = future.result()
            if success:
                results['success'].append(info)
            else:
                results['failed'].append((idx + 1, info))
    
    return results


def compress_images_to_zip(results, output_dir=None):
    """
    Compress successfully downloaded images into a zip file (directly from memory)
    
    Args:
        results (dict): Dictionary from download_all_parallel containing 'success' and 'failed' lists
        output_dir (str): Optional directory to save the zip file
        
    Returns:
        str: Path to the created zip file, or None if failed
    """
    # Get successfully downloaded images
    image_data_list = results.get('success', [])
    
    if not image_data_list:
        return None
    
    # Create zip filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"images_{timestamp}.zip"
    
    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        zip_filename = os.path.join(output_dir, zip_filename)
    
    # Create zip file directly from memory
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_info in image_data_list:
                # Write data directly to zip without saving to disk
                zipf.writestr(image_info['filename'], image_info['data'])
        
        return zip_filename
    
    except Exception as e:
        return None


def compress_images_to_django_file(results):
    """
    Compress successfully downloaded images into a zip file in memory
    and return as Django File object for FileField
    
    Args:
        results (dict): Dictionary from download_all_parallel containing 'success' and 'failed' lists
        
    Returns:
        tuple: (Django File object, filename) or (None, None) if failed
    """
    from io import BytesIO
    from django.core.files.base import ContentFile
    
    # Get successfully downloaded images
    image_data_list = results.get('success', [])
    
    if not image_data_list:
        return None, None
    
    # Create zip filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"images_{timestamp}.zip"
    
    # Create zip file in memory
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_info in image_data_list:
                # Write data directly to zip
                zipf.writestr(image_info['filename'], image_info['data'])
        
        # Get the zip data
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        
        # Create Django File object
        django_file = ContentFile(zip_data, name=zip_filename)
        
        return django_file, zip_filename
    
    except Exception as e:
        return None, None



def download_and_compress_images(content_json, base_url, max_workers=3, output_dir=None):
    """
    Complete process to download images from JSON content and compress to zip
    
    Args:
        content_json (str): JSON string containing array of image URLs
        base_url (str): Base URL for the images
        max_workers (int): Number of parallel download threads
        output_dir (str): Optional directory to save the zip file
        
    Returns:
        dict: Result dictionary with success status, zip path, and statistics
    """
    try:
        # Parse JSON content to list
        image_urls = json.loads(content_json)
        
        if not isinstance(image_urls, list) or not image_urls:
            return {
                'success': False,
                'error': 'Invalid or empty image URLs list'
            }
        
        # Download all images in parallel
        download_results = download_all_parallel(image_urls, base_url, max_workers)
        
        # Compress to zip
        zip_path = compress_images_to_zip(download_results, output_dir)
        
        if zip_path:
            return {
                'success': True,
                'zip_path': zip_path,
                'total_images': len(image_urls),
                'downloaded': len(download_results['success']),
                'failed': len(download_results['failed'])
            }
        else:
            return {
                'success': False,
                'error': 'Failed to create zip file',
                'total_images': len(image_urls),
                'downloaded': len(download_results['success']),
                'failed': len(download_results['failed'])
            }
            
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'Invalid JSON format in content'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
