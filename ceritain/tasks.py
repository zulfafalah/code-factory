"""
Celery tasks for StoryNarration processing.
"""
from celery import shared_task
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_story_narration_task(self, story_narration_id):
    """
    Background task to process story narration.
    
    Args:
        story_narration_id (int): ID of the StoryNarration instance
        
    Returns:
        dict: Result of the operation
    """
    StoryNarration = apps.get_model('ceritain', 'StoryNarration')
    
    try:
        story_narration = StoryNarration.objects.get(id=story_narration_id)
        
        logger.info(f"Starting background processing for StoryNarration ID: {story_narration_id}")
        
        # Import service function
        from .services import process_story_narration
        process_story_narration(story_narration)
        
        logger.info(f"Successfully processed StoryNarration ID: {story_narration_id}")
        
        return {
            'success': True,
            'story_narration_id': story_narration_id,
            'message': 'Processing completed successfully'
        }
        
    except StoryNarration.DoesNotExist:
        logger.error(f"StoryNarration with ID {story_narration_id} not found")
        return {
            'success': False,
            'story_narration_id': story_narration_id,
            'error': f'StoryNarration with ID {story_narration_id} not found'
        }
        
    except Exception as e:
        logger.exception(f"Error processing StoryNarration ID: {story_narration_id}")
        
        # Update status to failed before retry
        try:
            story_narration = StoryNarration.objects.get(id=story_narration_id)
            story_narration.status = 'failed'
            story_narration.message_response = f"Processing failed: {str(e)}"
            story_narration.save(update_fields=['status', 'message_response'])
        except Exception:
            pass
        
        # Retry after 60 seconds
        raise self.retry(exc=e, countdown=60)
