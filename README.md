# MoodakLyom

MoodakLyom is a mobile-first mood app with:

- A FastAPI backend for auth, moods, tasks, profile data, tips, voice transcription, and multimodal mood analysis
- An Android frontend built with Kotlin, Jetpack Compose, Retrofit, and DataStore

## Setup

```bash
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

For local development tools and tests:

```bash
.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Run the backend:

```bash
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Health checks:

```bash
curl http://localhost:8000/health
```

## AI Pipeline

The backend now exposes two voice-related paths:

- `POST /voice/transcribe`
  Returns transcription only. This endpoint is kept stable for the Android app.
- `POST /mood/analyze`
  Returns transcript, text emotion, acoustic emotion, fused final mood, and degradation warnings when a branch fails.

Related text-only routes:

- `POST /emotion/analyze`
- `GET /emotion/health`

### Architecture

```text
audio upload
    |
    v
POST /mood/analyze
    |
    +--> multipart parse + temp file
    |
    +--> transcription
    |      |
    |      +--> OpenAI audio API
    |      +--> Azure OpenAI audio API
    |      +--> fallback text via env var
    |
    +--> text emotion
    |      |
    |      +--> local BERT classifier (primary)
    |      +--> external emotion API (fallback)
    |      +--> keyword detector (last fallback)
    |
    +--> acoustic emotion
    |      |
    |      +--> wav2vec2 speech-emotion classifier
    |
    +--> weighted late fusion
           |
           +--> shared taxonomy:
               happy, sad, angry, fearful, surprised, disgusted, neutral
```

### `/voice/transcribe`

Request:

- `multipart/form-data`
- file field: `audio_file`
- optional field: `language`

Response:

```json
{
  "success": true,
  "text": "I feel better now",
  "message": null
}
```

### `/mood/analyze`

Request:

- `multipart/form-data`
- file field: `audio_file`
- optional field: `language`

Response:

```json
{
  "mood": "happy",
  "confidence": 0.78,
  "distribution": {
    "happy": 0.78,
    "neutral": 0.12
  },
  "transcript": "I am doing well",
  "text_emotion": {
    "label": "happy",
    "confidence": 0.81,
    "distribution": {
      "happy": 0.81,
      "surprised": 0.19
    },
    "source": "bert"
  },
  "acoustic_emotion": {
    "label": "neutral",
    "confidence": 0.64,
    "distribution": {
      "neutral": 0.64,
      "happy": 0.36
    },
    "source": "acoustic"
  },
  "sarcasm_suspected": false,
  "language": "en",
  "processing_ms": 154,
  "degraded": false,
  "warnings": []
}
```

If transcription, text emotion, or acoustic emotion fails, the endpoint returns partial results with:

- `degraded: true`
- a populated `warnings` array

The route does not 500 on a single-branch failure.

## Environment Variables

### Core

- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_DAYS`

### Transcription

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_AUDIO_TRANSCRIPTION_URL`
- `OPENAI_TRANSCRIPTION_MODEL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_WHISPER_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`
- `TRANSCRIPTION_FALLBACK_TEXT`

### Text Emotion

- `EMOTION_MODEL_NAME`
- `EMOTION_API_URL`
- `EMOTION_API_TIMEOUT`
- `HF_HOME`

### Acoustic Emotion

- `ACOUSTIC_EMOTION_MODEL_NAME`
- `ACOUSTIC_EMOTION_SAMPLE_RATE`

### Fusion

- `FUSION_AUDIO_WEIGHT`
- `FUSION_TEXT_WEIGHT`

Default fusion weights:

- audio: `0.6`
- text: `0.4`

## Design Decisions

### Text Emotion Routing

- Primary: BERT classifier
  - If `app/models/bert_emotion_model` contains valid local artifacts, it is used first
  - If the local directory is missing weights or contains Git LFS pointer stubs, the loader falls back to `EMOTION_MODEL_NAME`
- Fallback: external emotion API configured by `EMOTION_API_URL`
- Last fallback: lightweight keyword detector

Why this order:

- The local BERT model keeps the default path self-contained
- Invalid local model assets are skipped rather than silently shadowing a valid remote model
- The external API remains available as a backup integration
- The keyword fallback keeps the endpoint responsive even if model dependencies or remote services are unavailable

### Multimodal Fusion

- The acoustic branch uses a pretrained wav2vec2 speech-emotion model
- Text and acoustic outputs are projected onto one shared taxonomy
- Final mood is computed with weighted late fusion
- `sarcasm_suspected` is set to `true` when text and tone disagree and both branches are confident (`> 0.6`)

## Tests

Run:

```bash
.venv\Scripts\python -m pytest --cov=app.services.fusion --cov=app.services.text_emotion --cov=app.routes.mood_routes --cov-report=term-missing
```

Current coverage target met for:

- `app/services/fusion.py`
- `app/services/text_emotion.py`
- `app/routes/mood_routes.py`

## Deployment

### Environment

Start from `.env.example` and set at minimum:

- `SECRET_KEY`
- `DATABASE_URL`
- `CORS_ALLOW_ORIGINS`

Optional AI-specific settings:

- `EMOTION_MODEL_NAME`
- `EMOTION_API_URL`
- `FASTER_WHISPER_MODEL`
- `ACOUSTIC_EMOTION_MODEL_NAME`
- `HF_HOME`

### Docker

Backend container image:

```bash
docker build -f Dockerfile.backend -t moodaklyom-backend .
```

Run it:

```bash
docker run --rm -p 8000:8000 --env-file .env -v moodaklyom-data:/app/data -v moodaklyom-hf:/hf-cache moodaklyom-backend
```

### Operational Notes

- The acoustic model artifact is large, roughly `1.26 GB`, and should be cached in a persistent Hugging Face cache volume.
- The acoustic branch requires materially more memory than the text branch. Plan for several gigabytes of RAM plus swap/page file headroom on CPU-only hosts.
- `EMOTION_API_URL` is optional and unset by default. The external fallback is only attempted when explicitly configured.
- CORS is origin-based and should be set explicitly with `CORS_ALLOW_ORIGINS` for each deployed frontend.

## Notes

- `/voice/transcribe` remains unchanged for Android compatibility.
- Local OpenAI Whisper is optional in code, but not part of the base `requirements.txt` because the clean Python 3.13 runtime path is built around API transcription, `TRANSCRIPTION_FALLBACK_TEXT`, and `faster-whisper` support already present elsewhere in the repo.
