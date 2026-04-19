"""
Speech-to-Text Service
Ultra-fast + accurate transcription using faster-whisper (cross-platform: M1/M2/M3 macs, Windows, Linux).
"""

import os
import asyncio
from typing import Optional
from dotenv import load_dotenv
import ffmpeg
import platform
import torch

load_dotenv()

# -------------------------------
# CONFIG
# -------------------------------
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")  # medium = good speed/accuracy balance
_cached_model = None

# -------------------------------
# DEVICE & COMPUTE TYPE
# -------------------------------
def get_device_and_compute():
    system = platform.system()
    if system == "Darwin" and torch.backends.mps.is_available():
        return "mps", "float16"  # Apple GPU
    elif torch.cuda.is_available():
        return "cuda", "float16"  # NVIDIA GPU
    else:
        return "cpu", "int8"      # CPU fallback

# -------------------------------
# AUDIO PREPROCESSING
# -------------------------------
def preprocess_audio(input_path: str) -> str:
    """
    Convert audio to clean 16kHz mono PCM WAV (best for Whisper accuracy).
    """
    clean_path = input_path + "_clean.wav"

    (
        ffmpeg
        .input(input_path)
        .output(clean_path, ac=1, ar=16000, c="pcm_s16le")
        .overwrite_output()
        .run(quiet=True)
    )

    return clean_path

# -------------------------------
# PUBLIC TRANSCRIPTION
# -------------------------------
async def transcribe_audio(audio_file_path: str, language: Optional[str] = "en") -> str:
    """
    Transcribe an audio file using local faster-whisper (cross-platform, free).
    """
    try:
        return await _transcribe_with_faster_whisper(audio_file_path, language)
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

# -------------------------------
# LOCAL MODE — FASTER-WHISPER
# -------------------------------
async def _transcribe_with_faster_whisper(audio_file_path: str, language: Optional[str]) -> str:
    global _cached_model
    from faster_whisper import WhisperModel

    # 1. Preprocess audio
    clean_audio = preprocess_audio(audio_file_path)

    # 2. Load model once
    if _cached_model is None:
        device, compute_type = get_device_and_compute()
        print(f"Loading faster-whisper model '{WHISPER_MODEL}' on device '{device}' with compute_type='{compute_type}' ...")

        _cached_model = WhisperModel(
            WHISPER_MODEL,
            device=device,
            compute_type=compute_type,
        )

        print(f"✅ Model '{WHISPER_MODEL}' loaded!")

    # 3. Transcribe in thread pool (sync → async)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: _run_faster_whisper(_cached_model, clean_audio, language)
    )

# -------------------------------
# RUN FASTER-WHISPER
# -------------------------------
def _run_faster_whisper(model, audio_path: str, language: Optional[str]) -> str:
    """
    Beam-search transcription, temperature=0 for accuracy, VAD filtering for silence.
    """

    segments, info = model.transcribe(
    audio_path,
    language=language,
    beam_size=1,
    temperature=0.0,
    vad_filter=True
    )


    text_parts = [seg.text.strip() for seg in segments if seg.text.strip()]
    final_text = " ".join(text_parts).strip()

    print(f"DEBUG: Transcription result: {final_text[:100]}...")

    return final_text

# -------------------------------
# USAGE EXAMPLE
# -------------------------------
if __name__ == "__main__":
    import sys
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "example.wav"
    import asyncio
    text = asyncio.run(transcribe_audio(audio_path))
    print("Transcribed text:", text)
