from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StoryNarration
from .services import process_story_narration


@receiver(post_save, sender=StoryNarration)
def story_narration_post_save(sender, instance, created, **kwargs):
    """
    Signal handler called after StoryNarration is saved.
    Processes content if content_text is not empty.
    Uses transaction.on_commit() to ensure processing happens
    after the transaction is committed successfully.
    """
    # Only process on creation, not on every update
    if created:
        # Use on_commit to run after the transaction completes
        transaction.on_commit(lambda: process_story_narration(instance))

