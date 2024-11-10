
from manim_voiceover import VoiceoverScene

class CustomVoiceoverScene(VoiceoverScene):
    def set_speech_service(self, speech_service, create_subcaption=False):
        super().set_speech_service(speech_service, create_subcaption=create_subcaption)
