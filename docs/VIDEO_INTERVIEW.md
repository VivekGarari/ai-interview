# Video Interview — ProctoAI

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Describes the **video interview** modality — currently an audio-first prototype — and the roadmap
for a reliable, ethical communication analysis. Video is **deferred out of V1** (see
[V1_SCOPE](V1_SCOPE.md)) until the written/coding/evaluation foundation is reliable.

## 2. Non-negotiable framing

- The objective is to evaluate **interview performance** (clarity, communication, answer
  structure, pacing, filler usage, delivery, reasoning, technical correctness) — **not**
  personality, appearance, emotion, or psychological state.
- Claims around **emotion, personality, confidence, eye tracking, and psychological inference**
  are `[FUTURE]`/experimental. They must be treated as future capabilities unless actually
  implemented and validated.

## 3. Current implementation `[PARTIAL]` (audio-first)

### Backend (`app/routers/video.py`, `app/services/stt_services.py`, `tts_service.py`, `video_service.py`)

| Step | How it works today |
|------|--------------------|
| Session | `POST /video/start` creates an `InterviewSession` + first question; returns a TTS audio URL |
| Question audio | `GET /video/question/{id}/audio` — Edge TTS MP3 (**unauthenticated**) |
| Answer capture | Frontend records audio (webm). `POST /video/transcribe` (multipart) receives it |
| Speech-to-text | **Groq Whisper** (`stt_services.py`, whisper-large-v3) |
| Content evaluation | Same `evaluate_answer` used by the written interview (single LLM, 0–10) |
| Communication score | `video_service.analyze_transcript`: words/min, filler-word count/rate, pace bands (deterministic transcript heuristics) + `confidence_score` from an LLM text call |
| Final score | `content * 0.6 + communication * 0.4` per answer and for the session report |
| Next questions | Same uncontrolled `generate_question` (max 5) |
| Recording | `POST /video/upload-recording` saves webm to **local disk**; returns a URL with **no serving route** |

### Frontend (`src/pages/VideoInterviewPage.jsx`) — high risk

- **Uses non-standard browser APIs** (`navigator.mediaDevices.getUserMedia`, `MediaRecorder`,
  `recorder.ondataavailable`, `video.srcObject`). Assume this page does not work in mainstream
  browsers until verified (see [Architecture §15](ARCHITECTURE.md#15-repository-audit)).
- Camera stream is display-only; **no video analysis is performed**.
- Student answers are recorded as audio-only webm blobs and uploaded for transcription.

### Honest reading of the "confidence" score

`video_service._analyze_confidence` asks the LLM to rate the confidence of the **transcript
text**. It is:

- an LLM text heuristic (not a validated measure),
- dependent entirely on transcription quality,
- presented in the UI as `confidence_score`.

Per §2 it must be labelled as a heuristic where shown, or removed, until validated.

## 4. Gap analysis (current → target)

| Concern | Status |
|---------|--------|
| Speech-to-text | `[IMPLEMENTED]` (Groq Whisper) |
| Text-to-speech | `[IMPLEMENTED]` (Edge TTS) |
| Audio upload handling | `[PARTIAL]` — unbounded size, no validation |
| Recording persistence/playback | `[PARTIAL]` — local disk, URL dead (no GET route) |
| Communication metrics (pace, fillers) | `[IMPLEMENTED]` (transcript heuristics; quality depends on STT) |
| Structured interview evaluation | `[V1]` — delay video until shared evaluation core exists |
| Ethical/validated communication analysis | `[FUTURE]` |
| Real video analysis (visual / eye tracking / emotion) | `[IDEA]` — experimental only |

## 5. Target (post-V1)

1. **Audio pipeline hardened:** bounded uploads, content-type checks, object-storage persistence
   (S3), authenticated retrieval.
2. **Shared evaluation core:** video sessions reuse the stored-question + structured-evaluation
   engines from written/coding. Only the capture path (STT) and communication metrics are video-specific.
3. **Validated communication metrics:** calibrated WPM/filler/pace models; any
   confidence-style signal must be validated or clearly experimental.
4. Only then consider richer signals (`[IDEA]`): tone-of-voice features, video-based delivery
   signals — each gated and ethically reviewed.

## 6. V1 recommendation

- Keep the video prototype **gated/experimental** (or hidden) during V1.
- Do not invest in video UI until the written + coding + evaluation foundation is proven.
- When resumed: reuse session/evaluation core; add speech layer; remove the "confidence" number
  or relabel it as an experimental heuristic.

## 7. Open decisions

1. Fix the media-capture frontend (supported APIs) vs hide the video page for the next release.
2. STT/TTS provider strategy when resumed (Groq STT + Edge TTS today; keep or swap).
3. Object storage provider for recordings when resumed (S3 vs alternatives).