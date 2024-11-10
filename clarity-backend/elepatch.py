import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import base64
import random

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover.helper import create_dotenv_file, remove_bookmarks
from manim_voiceover.services.base import SpeechService

# List of voice IDs to choose from
VOICE_IDS = [
    "repzAAjoKlgcT2oOAIWt",
    "1BUhH8aaMvGMUdGAmWVM",
]

class VoiceSettings:
    def __init__(
        self,
        stability: float,
        similarity_boost: float,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ):
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.style = style
        self.use_speaker_boost = use_speaker_boost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost
        }

class Voice:
    def __init__(self, voice_id: str, name: str = "", settings: Optional[VoiceSettings] = None):
        self.voice_id = voice_id
        self.name = name
        self.settings = settings

class ElevenLabsService(SpeechService):
    """Speech service for ElevenLabs API."""
    
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        voice_name: Optional[str] = None,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        voice_settings: Optional[Union[VoiceSettings, dict]] = None,
        output_format: str = "mp3_44100_128",
        transcription_model: str = "base",
        **kwargs,
    ):
        """Initialize ElevenLabs service with direct API calls."""
        self.api_key = os.getenv("ELEVEN_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVEN_API_KEY environment variable not set")

        self.headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Get available voices
        response = requests.get(f"{self.BASE_URL}/voices", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch voices: {response.text}")
        
        available_voices = [
            Voice(v["voice_id"], v["name"]) 
            for v in response.json()["voices"]
        ]

        # Select voice based on name, ID, or random from list
        if voice_name:
            selected_voice = [v for v in available_voices if v.name == voice_name]
        elif voice_id:
            selected_voice = [v for v in available_voices if v.voice_id == voice_id]
        else:
            # Randomly select a voice ID from our list
            random_voice_id = random.choice(VOICE_IDS)
            selected_voice = [v for v in available_voices if v.voice_id == random_voice_id]
            logger.info(f"Randomly selected voice ID: {random_voice_id}")

        if selected_voice:
            self.voice = selected_voice[0]
            logger.info(f"Using voice: {self.voice.name} (ID: {self.voice.voice_id})")
        else:
            logger.warn(
                "Given voice_name/voice_id not found or random selection failed. "
                f"Defaulting to {available_voices[0].name}"
            )
            self.voice = available_voices[0]

        self.model = model

        # Handle voice settings
        if voice_settings:
            if isinstance(voice_settings, dict):
                if not voice_settings.get("stability") or not voice_settings.get("similarity_boost"):
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
            
            self.voice.settings = self.voice_settings
        
        self.output_format = output_format
        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs,
    ) -> dict:
        logger.info("=== Starting generate_from_text ===")
        
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "elevenlabs",
            "config": {
                "model": self.model,
                "voice": {
                    "voice_id": self.voice.voice_id,
                    "settings": self.voice.settings.to_dict() if self.voice.settings else None
                }
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
            # Regular TTS request first to get audio
            request_data = {
                "text": input_text,
                "model_id": self.model,
                "output_format": self.output_format,
            }
            
            if self.voice.settings:
                request_data["voice_settings"] = self.voice.settings.to_dict()

            # Get audio first
            headers = self.headers.copy()
            headers["Accept"] = "audio/mpeg"
            response = requests.post(
                f"{self.BASE_URL}/text-to-speech/{self.voice.voice_id}",
                json=request_data,
                headers=headers
            )

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.text}")

            # Save the audio
            output_path = Path(cache_dir) / audio_path
            output_path.write_bytes(response.content)

            # Now get word timings
            headers = self.headers.copy()
            response = requests.post(
                f"{self.BASE_URL}/text-to-speech/{self.voice.voice_id}/stream",
                json=request_data,
                headers=headers
            )

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.text}")

            # Process response to create word boundaries
            word_boundaries = []
            current_offset = 0
            
            # Split text into words and create simple timing
            words = input_text.split()
            total_duration = len(input_text) * 0.05  # Rough estimate
            time_per_word = total_duration / len(words)
            
            for i, word in enumerate(words):
                # Find actual offset in text
                while current_offset < len(input_text):
                    if input_text[current_offset:].startswith(word):
                        break
                    current_offset += 1
                
                word_boundaries.append({
                    "text_offset": current_offset,
                    "audio_offset": int(i * time_per_word * 1000),  # Convert to milliseconds
                    "word": word,
                    "start": i * time_per_word,
                    "end": (i + 1) * time_per_word
                })
                current_offset += len(word)

        except Exception as e:
            logger.error(f"ElevenLabs API Error: {str(e)}")
            raise Exception("Failed to generate audio with ElevenLabs.") from e

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "word_boundaries": word_boundaries,
            "final_audio": audio_path,  # Using same file for both
            "duration": total_duration
        }

        return json_dict

    def _wrap_generate_from_text(self, text: str, **kwargs) -> dict:
        """Keep the original audio file as is, since we already have word timings"""
        return self.generate_from_text(text, cache_dir=None, path=None, **kwargs)
