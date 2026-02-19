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
        story_narration_id (str): UUID of the StoryNarration instance
        
    Returns:
        dict: Result of the operation
    """
    StoryNarration = apps.get_model('ceritain', 'StoryNarration')
    
    try:
        story_narration = StoryNarration.objects.get(pk=story_narration_id)
        
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
            story_narration = StoryNarration.objects.get(pk=story_narration_id)
            story_narration.status = 'failed'
            story_narration.message_response = f"Processing failed: {str(e)}"
            story_narration.save(update_fields=['status', 'message_response'])
        except Exception:
            pass
        
        # Retry after 60 seconds
        raise self.retry(exc=e, countdown=60)


@shared_task
def reset_daily_token_usage():
    """
    Reset the total_token_used counter to 0 in StoryNarrationSettings.
    This task is intended to be called by Celery Beat on a daily schedule.
    
    Returns:
        dict: Result of the operation
    """
    StoryNarrationSettings = apps.get_model('ceritain', 'StoryNarrationSettings')
    
    try:
        settings = StoryNarrationSettings.get_solo()
        previous_value = settings.total_token_used
        settings.total_token_used = 0
        settings.save(update_fields=['total_token_used'])
        
        logger.info(f"Successfully reset total_token_used from {previous_value} to 0")
        
        return {
            'success': True,
            'previous_value': previous_value,
            'message': 'Daily token usage reset successfully'
        }
        
    except Exception as e:
        logger.exception("Error resetting daily token usage")
        return {
            'success': False,
            'error': str(e)
        }
