from typing import Dict, Any
import os
from kokoro_onnx import Kokoro
from src.utils.logger import logger

class VoiceOutSkill:
    """
    TTS Skill using Kokoro-82M for neural-quality local speech synthesis.
    """
    def __init__(self, model_path: str = "models/kokoro-v0_19.onnx", voices_path: str = "models/voices.json"):
        self.model_path = model_path
        self.voices_path = voices_path
        self.kokoro = None

    def _load_model(self):
        if self.kokoro is None:
            # We assume the user has downloaded the model files or we will provide instructions
            if not os.path.exists(self.model_path):
                logger.warning(f"Kokoro model not found at {self.model_path}. TTS will be disabled.")
                return False
            
            logger.info("Loading Kokoro TTS model...")
            self.kokoro = Kokoro(self.model_path, self.voices_path)
            return True
        return True

    def speak(self, text: str, voice: str = "af_heart") -> Dict[str, Any]:
        """Generates audio bytes from text."""
        if not self._load_model():
            return {"status": "error", "message": "TTS model not loaded"}
            
        try:
            # Kokoro generates a tuple of (samples, sample_rate)
            samples, sample_rate = self.kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
            # In a real app we might return the wav file or raw bytes
            return {"status": "success", "data": {"audio": samples.tobytes(), "sample_rate": sample_rate}, "message": "Speech generated"}
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return {"status": "error", "message": str(e)}

# Singleton for reuse
voice_tts = VoiceOutSkill()
