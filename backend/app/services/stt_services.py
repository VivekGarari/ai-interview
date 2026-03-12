import httpx
import tempfile
import os
from app.core.config import settings


class STTService:
    """
    Speech-to-Text using Groq's Whisper API (free with Groq key).
    Accepts audio bytes (webm, mp4, wav, mp3) and returns transcript.
    """

    GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm") -> dict:
        """
        Transcribe audio bytes to text using Groq Whisper.
        Returns dict with transcript, confidence, duration.
        """
        if not audio_bytes:
            return {"transcript": "", "success": False, "error": "No audio data"}

        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    self.GROQ_STT_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (filename, audio_bytes, "audio/webm")},
                    data={
                        "model": "whisper-large-v3",
                        "response_format": "verbose_json",
                        "language": "en",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "transcript": data.get("text", "").strip(),
                        "duration": data.get("duration", 0),
                        "success": True,
                        "error": None,
                    }
                else:
                    return {
                        "transcript": "",
                        "success": False,
                        "error": f"STT API error: {response.status_code}",
                    }

        except Exception as e:
            return {"transcript": "", "success": False, "error": str(e)}


stt_service = STTService()