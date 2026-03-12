import asyncio
import io
import edge_tts
from app.core.config import settings


class TTSService:
    """
    Text-to-Speech using Microsoft Edge TTS.
    Completely free, no API key needed, high quality voices.
    """

    VOICE = "en-US-GuyNeural"  # Professional male interviewer voice
    # Other good options:
    # "en-US-JennyNeural"     — friendly female
    # "en-GB-RyanNeural"      — British male
    # "en-US-AriaNeural"      — confident female
    INTERVIEWER_VOICE_ID = "en-US-GuyNeural"

    def __init__(self):
        self.enabled = True

    def synthesize(self, text: str, voice: str = None) -> bytes | None:
        """Convert text to MP3 audio bytes."""
        try:
            return asyncio.run(self._synthesize_async(text, voice or self.VOICE))
        except Exception as e:
            print(f"TTS error: {e}")
            return None

    async def _synthesize_async(self, text: str, voice: str) -> bytes:
        buffer = io.BytesIO()
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        return buffer.getvalue()

    def get_question_audio(self, question_text: str) -> bytes | None:
        return self.synthesize(question_text)


tts_service = TTSService()