from typing import Dict, Any
import os
from faster_whisper import WhisperModel
from src.utils.logger import logger

class VoiceInSkill:
    """
    STT Skill using Whisper v3 Turbo for high-speed local transcription.
    """
    def __init__(self, model_size: str = "deepdml/faster-whisper-large-v3-turbo-ct2"):
        # We use the turbo variant for <150ms latency as requested
        self.model_size = model_size
        self.model = None

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading Whisper Turbo model: {self.model_size}")
            # Run on CPU by default for portability, or GPU if available
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Transcribes a local audio file to text."""
        self._load_model()
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=1)
            text = " ".join([segment.text for segment in segments])
            return {"status": "success", "data": {"text": text.strip()}, "message": "Transcription complete"}
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return {"status": "error", "message": f"Error transcribing audio: {str(e)}"}

# Singleton for reuse
voice_stt = VoiceInSkill()
