from celery import shared_task
from django.apps import apps
from urllib.parse import urlparse
import json
import logging

from .utils import download_all_parallel, compress_images_to_django_file

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def download_and_compress_manhwa_images(self, manhwa_id, base_url=None, max_workers=3):
    """
    Background task to download and compress manhwa images
    
    Args:
        manhwa_id (int): ID of the Manhwa instance
        base_url (str): Base URL for images (optional)
        max_workers (int): Number of parallel download threads
        
    Returns:
        dict: Result of the operation
    """
    # Import here to avoid circular imports
    Manhwa = apps.get_model('kokorean', 'Manhwa')
    
    try:
        # Get the manhwa instance
        manhwa = Manhwa.objects.get(id=manhwa_id)
        
        logger.info(f"Starting download task for Manhwa ID: {manhwa_id}")
        
        # Update status to 'in progress'
        manhwa.download_status = 'in progress'
        manhwa.save(update_fields=['download_status'])
        
        # Parse content to get image URLs
        try:
            image_urls = json.loads(manhwa.content)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in content for Manhwa ID: {manhwa_id}")
            manhwa.download_status = 'failed'
            manhwa.save(update_fields=['download_status'])
            return {
                'success': False,
                'error': 'Invalid JSON format in content',
                'manhwa_id': manhwa_id
            }
        
        if not isinstance(image_urls, list) or not image_urls:
            logger.error(f"Empty or invalid image URLs for Manhwa ID: {manhwa_id}")
            manhwa.download_status = 'failed'
            manhwa.save(update_fields=['download_status'])
            return {
                'success': False,
                'error': 'Invalid or empty image URLs list',
                'manhwa_id': manhwa_id
            }
        
        
        logger.info(f"Downloading {len(image_urls)} images from {base_url}")
        
        # Download all images in parallel
        download_results = download_all_parallel(image_urls, base_url, max_workers)
        
        logger.info(f"Downloaded {len(download_results['success'])} of {len(image_urls)} images")
        
        # Compress to Django File object
        django_file, zip_filename = compress_images_to_django_file(download_results)
        
        if django_file:
            # Save zip file to model
            manhwa.zip_file.save(zip_filename, django_file, save=False)
            manhwa.download_status = 'completed'
            manhwa.save()
            
            logger.info(f"Successfully completed download for Manhwa ID: {manhwa_id}")
            
            return {
                'success': True,
                'manhwa_id': manhwa_id,
                'zip_filename': zip_filename,
                'total_images': len(image_urls),
                'downloaded': len(download_results['success']),
                'failed': len(download_results['failed'])
            }
        else:
            logger.error(f"Failed to compress images for Manhwa ID: {manhwa_id}")
            manhwa.download_status = 'failed'
            manhwa.save(update_fields=['download_status'])
            
            return {
                'success': False,
                'error': 'Failed to compress images',
                'manhwa_id': manhwa_id,
                'total_images': len(image_urls),
                'downloaded': len(download_results['success']),
                'failed': len(download_results['failed'])
            }
    
    except Manhwa.DoesNotExist:
        logger.error(f"Manhwa with ID {manhwa_id} not found")
        return {
            'success': False,
            'error': f'Manhwa with ID {manhwa_id} not found'
        }
    
    except Exception as e:
        logger.exception(f"Error in download task for Manhwa ID: {manhwa_id}")
        
        try:
            manhwa = Manhwa.objects.get(id=manhwa_id)
            manhwa.download_status = 'failed'
            manhwa.save(update_fields=['download_status'])
        except:
            pass
        
        # Retry the task if it failed
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds
