import os
import sys
from pathlib import Path
from typing import List, Optional, Union

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover.helper import create_dotenv_file, remove_bookmarks
from manim_voiceover.services.base import SpeechService

try:
    from elevenlabs import Voice, VoiceSettings, play
    from elevenlabs import ElevenLabs
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[elevenlabs]"` '
        "to use ElevenLabs API."
    )

load_dotenv(find_dotenv(usecwd=True))

def create_dotenv_elevenlabs():
    logger.info(
        "Check out https://voiceover.manim.community/en/stable/services.html#elevenlabs"
        " to learn how to create an account and get your subscription key."
    )
    try:
        os.environ["ELEVEN_API_KEY"]
    except KeyError:
        if not create_dotenv_file(["ELEVEN_API_KEY"]):
            raise Exception(
                "The environment variables ELEVEN_API_KEY are not set. "
                "Please set them or create a .env file with the variables."
            )
        logger.info("The .env file has been created. Please run Manim again.")
        sys.exit()

create_dotenv_elevenlabs()

class ElevenLabsService(SpeechService):
    """Speech service for ElevenLabs API."""

    def __init__(
        self,
        voice_name: Optional[str] = None,
        voice_id: Optional[str] = "TCc853ooY510KrvEBVqz",
        model: str = "eleven_multilingual_v2",  # Updated default model
        voice_settings: Optional[Union["VoiceSettings", dict]] = None,
        output_format: str = "mp3_44100_128",
        transcription_model: str = "base",
        **kwargs,
    ):
        """Initialize ElevenLabs client and voice settings."""
        # Initialize ElevenLabs client
        self.client = ElevenLabs()
        
        # Get available voices
        response = self.client.voices.get_all()
        available_voices: List[Voice] = response.voices

        # Select voice based on name or ID
        if voice_name:
            selected_voice = [v for v in available_voices if v.name == voice_name]
        elif voice_id:
            selected_voice = [v for v in available_voices if v.voice_id == voice_id]
        else:
            selected_voice = None
            logger.warn(
                "None of `voice_name` or `voice_id` provided. "
                "Will be using default voice."
            )

        if selected_voice:
            self.voice = selected_voice[0]
        else:
            logger.warn(
                "Given `voice_name` or `voice_id` not found (or not provided). "
                f"Defaulting to {available_voices[0].name}"
            )
            self.voice = available_voices[0]

        self.model = model

        # Handle voice settings
        if voice_settings:
            if isinstance(voice_settings, dict):
                if not voice_settings.get("stability") or not voice_settings.get(
                    "similarity_boost"
                ):
                    raise KeyError(
                        "Missing required keys: 'stability' and 'similarity_boost'. "
                        "Required for setting voice setting"
                    )
                self.voice_settings = VoiceSettings(
                    stability=voice_settings["stability"],
                    similarity_boost=voice_settings["similarity_boost"],
                    style=voice_settings.get("style", 0),
                    use_speaker_boost=voice_settings.get("use_speaker_boost", True),
                )
            elif isinstance(voice_settings, VoiceSettings):
                self.voice_settings = voice_settings
            else:
                raise TypeError(
                    "voice_settings must be a VoiceSettings object or a dictionary"
                )

            # Apply voice settings
            self.voice = Voice(
                voice_id=self.voice.voice_id,
                settings=self.voice_settings
            )

        self.output_format = output_format
        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Generate audio from text using ElevenLabs API."""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "elevenlabs",
            "config": {
                "model": self.model,
                "voice": self.voice.model_dump(exclude_none=True),
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        try:
            # Generate audio using new API
            audio = self.client.generate(
                text=input_text,
                voice=self.voice,
                model=self.model,
                output_format=self.output_format,
            )
            
            # Save the generated audio
            with open(str(Path(cache_dir) / audio_path), "wb") as f:
                f.write(audio)

        except Exception as e:
            logger.error(e)
            raise Exception("Failed to generate audio with ElevenLabs.")

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict 
