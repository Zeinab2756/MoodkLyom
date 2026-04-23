from __future__ import annotations

import time
import wave
from pathlib import Path

from app.schemas.emotion_schemas import EmotionDistribution

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _frame_count(audio_path: str | Path) -> int:
    with wave.open(str(audio_path), "rb") as wav_file:
        return wav_file.getnframes()


def _post_audio(client, token: str, fixture_name: str):
    file_path = FIXTURES_DIR / fixture_name
    with file_path.open("rb") as audio_file:
        return client.post(
            "/mood/analyze",
            headers={"Authorization": f"Bearer {token}"},
            data={"language": "en"},
            files={"audio_file": (file_path.name, audio_file, "audio/wav")},
        )


def _happy_text_emotion() -> EmotionDistribution:
    return EmotionDistribution(
        label="joy",
        confidence=0.91,
        distribution={"joy": 0.91, "surprise": 0.09},
        source="bert",
    )


def _neutral_text_emotion() -> EmotionDistribution:
    return EmotionDistribution(
        label="neutral",
        confidence=0.55,
        distribution={"neutral": 0.55, "sad": 0.45},
        source="bert",
    )


def _happy_acoustic_emotion() -> EmotionDistribution:
    return EmotionDistribution(
        label="happy",
        confidence=0.84,
        distribution={"happy": 0.84, "neutral": 0.16},
        source="acoustic",
    )


def _angry_acoustic_emotion() -> EmotionDistribution:
    return EmotionDistribution(
        label="angry",
        confidence=0.89,
        distribution={"angry": 0.89, "neutral": 0.11},
        source="acoustic",
    )


def _neutral_acoustic_emotion() -> EmotionDistribution:
    return EmotionDistribution(
        label="neutral",
        confidence=0.7,
        distribution={"neutral": 0.7, "sad": 0.3},
        source="acoustic",
    )


def _patch_pipeline(monkeypatch):
    def fake_transcribe(audio_path: str, language: str | None = None):
        frames = _frame_count(audio_path)
        if frames <= 2000:
            return True, "I feel happy today", None
        if frames <= 4000:
            return True, "I feel happy today", None
        return False, None, "mock transcription failed"

    def fake_text_emotion(transcript: str):
        if "happy" in transcript:
            return _happy_text_emotion()
        return _neutral_text_emotion()

    def fake_acoustic_emotion(audio_path: str):
        frames = _frame_count(audio_path)
        if frames <= 2000:
            return _happy_acoustic_emotion()
        if frames <= 4000:
            return _angry_acoustic_emotion()
        return _neutral_acoustic_emotion()

    monkeypatch.setattr("app.routes.mood_routes.transcribe_audio_file", fake_transcribe)
    monkeypatch.setattr("app.routes.mood_routes.predict_text_emotion", fake_text_emotion)
    monkeypatch.setattr("app.routes.mood_routes.predict_acoustic_emotion", fake_acoustic_emotion)


def test_mood_analyze_happy_path_returns_documented_schema(client, auth_token, monkeypatch):
    _patch_pipeline(monkeypatch)

    response = _post_audio(client, auth_token, "happy_short.wav")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "mood",
        "confidence",
        "distribution",
        "transcript",
        "text_emotion",
        "acoustic_emotion",
        "sarcasm_suspected",
        "language",
        "processing_ms",
        "degraded",
        "warnings",
    }
    assert payload["mood"] == "happy"
    assert payload["processing_ms"] > 0


def test_mood_analyze_parallel_execution_is_meaningfully_faster_than_sequential(client, auth_token, monkeypatch):
    def fake_transcribe(_audio_path: str, language: str | None = None):
        time.sleep(0.2)
        return True, "I feel happy today", None

    def fake_text_emotion(_transcript: str):
        time.sleep(0.35)
        return _happy_text_emotion()

    def fake_acoustic_emotion(_audio_path: str):
        time.sleep(0.35)
        return _happy_acoustic_emotion()

    monkeypatch.setattr("app.routes.mood_routes.transcribe_audio_file", fake_transcribe)
    monkeypatch.setattr("app.routes.mood_routes.predict_text_emotion", fake_text_emotion)
    monkeypatch.setattr("app.routes.mood_routes.predict_acoustic_emotion", fake_acoustic_emotion)

    started = time.perf_counter()
    response = _post_audio(client, auth_token, "happy_short.wav")
    elapsed = time.perf_counter() - started
    sequential_time = 0.2 + 0.35 + 0.35

    assert response.status_code == 200
    assert elapsed <= sequential_time * 0.7


def test_mood_analyze_gracefully_degrades_when_transcription_fails(client, auth_token, monkeypatch):
    def fake_transcribe(_audio_path: str, language: str | None = None):
        raise RuntimeError("transcription branch exploded")

    monkeypatch.setattr("app.routes.mood_routes.transcribe_audio_file", fake_transcribe)
    monkeypatch.setattr("app.routes.mood_routes.predict_acoustic_emotion", lambda path: _neutral_acoustic_emotion())
    monkeypatch.setattr("app.routes.mood_routes.predict_text_emotion", lambda text: _happy_text_emotion())

    response = _post_audio(client, auth_token, "happy_short.wav")

    assert response.status_code == 200
    payload = response.json()
    assert payload["degraded"] is True
    assert payload["text_emotion"] is None
    assert payload["acoustic_emotion"]["label"] == "neutral"
    assert any("Transcription failed" in warning for warning in payload["warnings"])


def test_mood_analyze_gracefully_degrades_when_acoustic_fails(client, auth_token, monkeypatch):
    monkeypatch.setattr("app.routes.mood_routes.transcribe_audio_file", lambda path, language=None: (True, "I feel happy today", None))
    monkeypatch.setattr("app.routes.mood_routes.predict_text_emotion", lambda text: _happy_text_emotion())

    def fake_acoustic(_audio_path: str):
        raise RuntimeError("acoustic branch exploded")

    monkeypatch.setattr("app.routes.mood_routes.predict_acoustic_emotion", fake_acoustic)

    response = _post_audio(client, auth_token, "happy_short.wav")

    assert response.status_code == 200
    payload = response.json()
    assert payload["degraded"] is True
    assert payload["text_emotion"]["label"] == "joy"
    assert payload["acoustic_emotion"] is None


def test_mood_analyze_returns_neutral_when_both_ai_branches_fail(client, auth_token, monkeypatch):
    monkeypatch.setattr("app.routes.mood_routes.transcribe_audio_file", lambda path, language=None: (True, "I feel happy today", None))

    def raise_text(_text: str):
        raise RuntimeError("text branch exploded")

    def raise_acoustic(_audio_path: str):
        raise RuntimeError("acoustic branch exploded")

    monkeypatch.setattr("app.routes.mood_routes.predict_text_emotion", raise_text)
    monkeypatch.setattr("app.routes.mood_routes.predict_acoustic_emotion", raise_acoustic)

    response = _post_audio(client, auth_token, "happy_short.wav")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mood"] == "neutral"
    assert payload["confidence"] <= 0.1
    assert payload["degraded"] is True
    assert len(payload["warnings"]) >= 2


def test_mood_analyze_rejects_invalid_upload_content(client, auth_token):
    response = client.post(
        "/mood/analyze",
        headers={"Authorization": f"Bearer {auth_token}"},
        data={"language": "en"},
        files={"audio_file": ("fake.wav", b"not actually a wav", "audio/wav")},
    )

    assert response.status_code == 400


def test_mood_analyze_missing_file_returns_422(client, auth_token):
    response = client.post(
        "/mood/analyze",
        headers={"Authorization": f"Bearer {auth_token}"},
        data={"language": "en"},
    )

    assert response.status_code == 422


def test_mood_analyze_rejects_oversized_audio(client, auth_token):
    response = _post_audio(client, auth_token, "oversized_31s.wav")

    assert response.status_code == 413
