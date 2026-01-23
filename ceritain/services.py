"""
Service layer for StoryNarration.
Contains processing logic for story narration.
"""

import logging
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from openai import OpenAI

logger = logging.getLogger(__name__)


def process_story_narration(story_narration):
    """
    Main function to process StoryNarration.
    Called by signal after model is saved.
    
    Args:
        story_narration: StoryNarration instance to be processed
    """
    # Check if source_url exists
    if story_narration.source_url:
        # Process from URL
        process_from_url(story_narration)
    else:
        # Process from content_text directly
        process_from_content(story_narration)


def process_from_url(story_narration):
    """
    Function to process StoryNarration from source_url.
    Will fetch content from URL and process it.
    
    Args:
        story_narration: StoryNarration instance with source_url
    """
    # TODO: Implement logic to fetch content from URL
    # - Fetch content from URL
    # - Parse and extract text
    # - Update content_text if needed
    # - Further processing
    pass


def process_from_content(story_narration):
    """
    Function to process StoryNarration from content_text directly.
    Converts content_text to speech using OpenAI TTS API.
    
    Args:
        story_narration: StoryNarration instance with content_text
    """
    try:
        # Update status to processing
        story_narration.status = 'processing'
        story_narration.save(update_fields=['status'])
        
        # Get content text
        content_text = story_narration.content_text
        
        if not content_text:
            logger.warning(f"StoryNarration {story_narration.id} has no content_text")
            story_narration.status = 'failed'
            story_narration.save(update_fields=['status'])
            return
        
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # TTS instructions for voice style
        instructions = """Voice Affect: Calm, composed, and reassuring; project quiet authority and confidence.

Tone: Sincere, empathetic, and gently authoritative—express genuine care while conveying competence.

Pacing: Steady and moderate; unhurried enough to communicate care, yet efficient enough to demonstrate professionalism.

Emotion: Genuine empathy and understanding; speak with warmth.

Pronunciation: Clear and precise, emphasizing key points to reinforce engagement.

Pauses: Brief pauses after important points, highlighting key information."""

        # Generate speech using OpenAI TTS API
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="nova",
            input=content_text,
            instructions=instructions,
            response_format="mp3",
        )
        
        # Get audio content
        audio_content = response.content
        
        # Generate unique filename
        filename = f"narration_{story_narration.id}_{uuid.uuid4().hex[:8]}.mp3"
        
        # Save audio file to result_file field
        story_narration.result_file.save(
            filename,
            ContentFile(audio_content),
            save=False
        )
        
        # Estimate token usage
        # OpenAI TTS API doesn't return token counts directly
        # We estimate based on text length (roughly 4 chars per token)
        input_tokens = len(content_text) // 4
        instruction_tokens = len(instructions) // 4
        total_input_tokens = input_tokens + instruction_tokens
        
        # Output tokens are estimated based on audio duration
        # For TTS, we can estimate ~150 words per minute, ~0.75 tokens per word
        word_count = len(content_text.split())
        estimated_output_tokens = int(word_count * 0.75)
        
        # Update token counts
        story_narration.input_token = total_input_tokens
        story_narration.output_token = estimated_output_tokens
        story_narration.total_token = total_input_tokens + estimated_output_tokens
        
        # Update final_content with info about the generated audio
        story_narration.final_content = f"Audio generated successfully. File: {filename}"
        
        # Update status to done
        story_narration.status = 'done'
        
        # Save all changes
        story_narration.save(update_fields=[
            'result_file',
            'input_token',
            'output_token', 
            'total_token',
            'final_content',
            'status'
        ])
        
        logger.info(f"StoryNarration {story_narration.id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing StoryNarration {story_narration.id}: {str(e)}")
        # Use update() to avoid transaction issues - this creates a new query
        from .models import StoryNarration
        StoryNarration.objects.filter(id=story_narration.id).update(
            status='failed',
            final_content=f"Error: {str(e)}"
        )


