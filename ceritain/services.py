"""
Service layer for StoryNarration.
Contains processing logic for story narration.
"""

import logging
import os
import tempfile
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from openai import OpenAI
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

logger = logging.getLogger(__name__)

# Default BGM path - can be overridden in settings
DEFAULT_BGM_PATH = getattr(settings, 'STORY_NARRATION_BGM_PATH', None)


def process_story_narration(story_narration):
    """
    Main function to process StoryNarration.
    Called by signal after model is saved.
    
    Args:
        story_narration: StoryNarration instance to be processed
    """
    from .models import StoryNarrationSettings

    # Check for maintenance mode
    try:
        settings = StoryNarrationSettings.get_solo()
        if settings.is_maintenance:
            logger.info(f"Maintenance mode active. Skipping StoryNarration {story_narration.id}")
            story_narration.message_response = "System is currently under maintenance. Please try again later."
            story_narration.status = 'failed'
            story_narration.save(update_fields=['message_response', 'status'])
            return
    except Exception as e:
        logger.error(f"Error checking maintenance mode: {e}")
        # Proceed with caution or fail? Assuming we proceed if check fails, or fail safe?
        # Let's proceed as this is likely a DB issue which will be caught later or harmless.
        pass

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


def mix_voice_with_bgm(voice_audio_bytes: bytes, bgm_path: str = None) -> bytes:
    """
    Mix voice narration with background music.
    
    Args:
        voice_audio_bytes: Raw audio bytes of the voice narration (MP3 format)
        bgm_path: Optional path to the background music file.
                  If not provided, uses DEFAULT_BGM_PATH from settings.
    
    Returns:
        bytes: Mixed audio content as MP3 bytes
    
    If no BGM path is provided or the file doesn't exist, 
    returns the original voice audio with basic processing.
    """
    # Load voice from bytes
    voice = AudioSegment.from_mp3(BytesIO(voice_audio_bytes))
    
    # ========== PROCESSING VOICE ==========
    # 1. Normalize voice (standardize volume)
    voice = normalize(voice)
    
    # 2. Dynamic compression for more consistent volume
    voice = compress_dynamic_range(voice, threshold=-20.0, ratio=4.0, attack=5.0)
    
    # 3. Add slight gain if needed
    voice = voice + 2  # +2 dB for clarity
    
    # 4. Fade in & fade out on voice for smooth transitions
    voice = voice.fade_in(1000).fade_out(2000)  # 1 second fade in, 2 seconds fade out
    
    # Determine BGM path to use
    bgm_file_path = bgm_path or DEFAULT_BGM_PATH
    
    # If no BGM path configured or file doesn't exist, return processed voice only
    if not bgm_file_path or not os.path.exists(bgm_file_path):
        logger.info("No BGM file available, returning processed voice only")
        # Export processed voice to bytes
        output_buffer = BytesIO()
        voice.export(
            output_buffer,
            format="mp3",
            bitrate="192k",
            parameters=["-q:a", "0"]
        )
        return output_buffer.getvalue()
    
    # ========== PROCESSING BGM ==========
    try:
        bgm = AudioSegment.from_mp3(bgm_file_path)
    except Exception as e:
        logger.warning(f"Failed to load BGM from {bgm_file_path}: {e}")
        # Return processed voice only
        output_buffer = BytesIO()
        voice.export(
            output_buffer,
            format="mp3",
            bitrate="192k",
            parameters=["-q:a", "0"]
        )
        return output_buffer.getvalue()
    
    # 1. Loop BGM if shorter than voice
    if len(bgm) < len(voice):
        loops_needed = (len(voice) // len(bgm)) + 1
        bgm = bgm * loops_needed
    
    # 2. Trim BGM to match voice duration
    bgm = bgm[:len(voice)]
    
    # 3. Lower BGM volume (-12 to -18 dB ideal for monologue)
    bgm = bgm - 12  # Softer than before
    
    # 4. Fade in & fade out BGM for smooth transitions
    bgm = bgm.fade_in(5000).fade_out(3000)  # 5 seconds fade in, 3 seconds fade out
    
    # 5. Apply additional ducking: BGM quieter when voice is active
    # Simple simulation - for best results use librosa or similar
    bgm = bgm - 3  # Additional volume reduction
    
    # ========== MIXING ==========
    # Overlay voice on top of BGM
    final_audio = bgm.overlay(voice)
    
    # ========== POST-PROCESSING ==========
    # Normalize final output to prevent clipping/distortion
    final_audio = normalize(final_audio)
    
    # Export with high bitrate for better audio quality
    output_buffer = BytesIO()
    final_audio.export(
        output_buffer,
        format="mp3",
        bitrate="192k",  # High bitrate for better quality
        parameters=["-q:a", "0"]  # Highest encoding quality
    )
    
    return output_buffer.getvalue()


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
        
        # Get audio content from TTS
        raw_audio_content = response.content
        
        # Mix voice with background music
        logger.info(f"Mixing voice with BGM for StoryNarration {story_narration.id}")
        audio_content = mix_voice_with_bgm(raw_audio_content)
        
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
        # Use update() to avoid transaction issues - this creates a new query
        from .models import StoryNarration, StoryNarrationSettings
        StoryNarration.objects.filter(id=story_narration.id).update(
            status='failed',
            final_content=f"Error: {str(e)}"
        )


