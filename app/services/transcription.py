from __future__ import annotations

import importlib.util
import json
import os
import urllib.error
import urllib.request
import uuid
from functools import lru_cache
from pathlib import Path


def _encode_multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[str, bytes]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []

    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(value.encode())
        parts.append(b"\r\n")

    for name, (filename, content, content_type) in files.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        parts.append(content)
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(parts)


def _transcribe_with_openai(audio_path: Path, language: str | None) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = os.getenv("OPENAI_AUDIO_TRANSCRIPTION_URL", f"{base_url}/audio/transcriptions")
    model = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
    fields = {"model": model}
    if language:
        fields["language"] = language
    boundary, body = _encode_multipart(
        fields=fields,
        files={"file": (audio_path.name, audio_path.read_bytes(), "application/octet-stream")},
    )

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError):
        return None

    return (payload.get("text") or "").strip() or None


def _transcribe_with_azure_openai(audio_path: Path, language: str | None) -> str | None:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    if not api_key or not endpoint or not deployment:
        return None

    endpoint = endpoint.rstrip("/")
    url = (
        f"{endpoint}/openai/deployments/{deployment}/audio/transcriptions"
        f"?api-version={api_version}"
    )
    fields: dict[str, str] = {}
    if language:
        fields["language"] = language
    boundary, body = _encode_multipart(
        fields=fields,
        files={"file": (audio_path.name, audio_path.read_bytes(), "application/octet-stream")},
    )

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError):
        return None

    return (payload.get("text") or "").strip() or None


@lru_cache(maxsize=1)
def _load_local_whisper_model():
    if importlib.util.find_spec("whisper") is None:
        return None

    import whisper

    model_name = os.getenv("WHISPER_MODEL", "base")
    return whisper.load_model(model_name)


def _transcribe_with_local_whisper(audio_path: Path, language: str | None) -> str | None:
    model = _load_local_whisper_model()
    if model is None:
        return None

    result = model.transcribe(str(audio_path), language=language or None)
    return (result.get("text") or "").strip() or None


@lru_cache(maxsize=1)
def _load_faster_whisper_model():
    if importlib.util.find_spec("faster_whisper") is None:
        return None

    from faster_whisper import WhisperModel

    model_name = os.getenv("FASTER_WHISPER_MODEL", os.getenv("WHISPER_MODEL", "tiny"))
    device = "cuda" if os.getenv("FASTER_WHISPER_DEVICE", "").lower() == "cuda" else "cpu"
    if device == "cpu":
        compute_type = os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "int8")
    else:
        compute_type = os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "float16")

    return WhisperModel(model_name, device=device, compute_type=compute_type)


def _transcribe_with_faster_whisper(audio_path: Path, language: str | None) -> str | None:
    model = _load_faster_whisper_model()
    if model is None:
        return None

    segments, _info = model.transcribe(str(audio_path), language=language or None)
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
    return text or None


def transcribe_audio_file(audio_path: str | Path, language: str | None = None) -> tuple[bool, str | None, str | None]:
    path = Path(audio_path)
    if not path.exists():
        return False, None, "Audio file not found"

    for provider in (
        _transcribe_with_openai,
        _transcribe_with_azure_openai,
        _transcribe_with_faster_whisper,
        _transcribe_with_local_whisper,
    ):
        text = provider(path, language)
        if text:
            return True, text, None

    fallback_text = os.getenv("TRANSCRIPTION_FALLBACK_TEXT")
    if fallback_text:
        return True, fallback_text, "Transcription backend is not configured"

    return False, None, "Transcription backend is not configured"
