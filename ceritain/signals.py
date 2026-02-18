from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StoryNarration


@receiver(post_save, sender=StoryNarration)
def story_narration_post_save(sender, instance, created, **kwargs):
    """
    Signal handler called after StoryNarration is saved.
    Triggers Celery task to process content asynchronously.
    Uses transaction.on_commit() to ensure task is queued
    after the transaction is committed successfully.
    """
    # Only process on creation, not on every update
    if created:
        from .tasks import process_story_narration_task
        # Use on_commit to queue task after transaction completes
        transaction.on_commit(lambda: process_story_narration_task.delay(str(instance.pk)))

