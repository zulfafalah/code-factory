from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StoryNarration
from .services import process_story_narration


@receiver(post_save, sender=StoryNarration)
def story_narration_post_save(sender, instance, created, **kwargs):
    """
    Signal handler called after StoryNarration is saved.
    Processes content if content_text is not empty.
    """
    # Skip if content_text is empty
    if not instance.content_text:
        return

    # Run process
    process_story_narration(instance)
