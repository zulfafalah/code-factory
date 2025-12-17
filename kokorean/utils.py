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
