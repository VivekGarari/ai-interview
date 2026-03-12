import re
from app.services.ai_service import ai_service


# Common filler words to detect
FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "honestly", "right", "so", "well", "kind of",
    "sort of", "i mean", "you see", "okay so",
]


class VideoAnalysisService:
    """
    Analyzes interview transcripts for communication quality.
    Detects filler words, estimates pace, and scores confidence.
    """

    def analyze_transcript(self, transcript: str, duration_seconds: int) -> dict:
        """
        Full analysis of a spoken answer transcript.
        Returns scores and detailed feedback.
        """
        if not transcript or not transcript.strip():
            return self._empty_analysis()

        words = transcript.split()
        word_count = len(words)

        # Words per minute
        wpm = round((word_count / duration_seconds) * 60) if duration_seconds > 0 else 0

        # Filler word analysis
        transcript_lower = transcript.lower()
        filler_counts = {}
        total_fillers = 0
        for filler in FILLER_WORDS:
            count = len(re.findall(r'\b' + re.escape(filler) + r'\b', transcript_lower))
            if count > 0:
                filler_counts[filler] = count
                total_fillers += count

        filler_rate = round((total_fillers / word_count) * 100, 1) if word_count > 0 else 0

        # Pace score (ideal is 120-160 wpm)
        if 120 <= wpm <= 160:
            pace_score = 10.0
        elif 100 <= wpm < 120 or 160 < wpm <= 180:
            pace_score = 8.0
        elif 80 <= wpm < 100 or 180 < wpm <= 200:
            pace_score = 6.0
        else:
            pace_score = 4.0

        # Filler word score
        if filler_rate < 2:
            filler_score = 10.0
        elif filler_rate < 5:
            filler_score = 8.0
        elif filler_rate < 10:
            filler_score = 6.0
        else:
            filler_score = 3.0

        # AI confidence analysis
        confidence_data = self._analyze_confidence(transcript)

        # Overall communication score
        overall = round((pace_score + filler_score + confidence_data["score"]) / 3, 1)

        return {
            "word_count": word_count,
            "duration_seconds": duration_seconds,
            "words_per_minute": wpm,
            "pace_score": pace_score,
            "pace_feedback": self._pace_feedback(wpm),
            "filler_words_found": filler_counts,
            "filler_word_count": total_fillers,
            "filler_rate_percent": filler_rate,
            "filler_score": filler_score,
            "confidence_score": confidence_data["score"],
            "confidence_feedback": confidence_data["feedback"],
            "overall_communication_score": overall,
            "summary": confidence_data["summary"],
        }

    def _pace_feedback(self, wpm: int) -> str:
        if wpm == 0:
            return "No speech detected."
        elif wpm < 80:
            return "Speaking too slowly. Try to pick up the pace a bit."
        elif wpm < 120:
            return "Slightly slow. A bit more energy would help."
        elif wpm <= 160:
            return "Great pace! Clear and easy to follow."
        elif wpm <= 180:
            return "Slightly fast. Slow down a little for clarity."
        else:
            return "Speaking too fast. Take a breath and slow down."

    def _analyze_confidence(self, transcript: str) -> dict:
        """Use AI to score confidence from transcript text."""
        try:
            system = """You are an expert communication coach analyzing interview responses.
Evaluate the speaker's confidence, clarity, and professionalism."""

            user = f"""Analyze this interview response transcript for confidence and communication quality:

"{transcript}"

Respond in this exact format:
SCORE: [0-10]
FEEDBACK: [one sentence about confidence/clarity]
SUMMARY: [one sentence overall communication assessment]"""

            response = ai_service._chat(system, user)

            score = 7.0
            feedback = "Good communication overall."
            summary = "Solid response with clear communication."

            for line in response.strip().split("\n"):
                if line.startswith("SCORE:"):
                    try:
                        score = float(line.replace("SCORE:", "").strip())
                    except ValueError:
                        pass
                elif line.startswith("FEEDBACK:"):
                    feedback = line.replace("FEEDBACK:", "").strip()
                elif line.startswith("SUMMARY:"):
                    summary = line.replace("SUMMARY:", "").strip()

            return {"score": score, "feedback": feedback, "summary": summary}

        except Exception:
            return {"score": 7.0, "feedback": "Good communication.", "summary": "Solid response."}

    def _empty_analysis(self) -> dict:
        return {
            "word_count": 0,
            "duration_seconds": 0,
            "words_per_minute": 0,
            "pace_score": 0,
            "pace_feedback": "No speech detected.",
            "filler_words_found": {},
            "filler_word_count": 0,
            "filler_rate_percent": 0,
            "filler_score": 0,
            "confidence_score": 0,
            "confidence_feedback": "No speech detected.",
            "overall_communication_score": 0,
            "summary": "No response provided.",
        }


video_analysis_service = VideoAnalysisService()