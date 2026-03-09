import os
from src.skills.voice_in import voice_stt
from src.skills.voice_out import voice_tts

class VoiceService:
    def __init__(self):
        self.max_upload_bytes = 10 * 1024 * 1024  # 10MB

    def transcribe(self, audio_data: bytes) -> str:
        temp_path = "temp_audio_v2.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        try:
            text = voice_stt.transcribe(temp_path)
            return text
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def speak(self, text: str) -> bytes:
        return voice_tts.speak(text)

voice_service = VoiceService()
