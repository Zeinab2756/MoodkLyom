from __future__ import annotations

import tempfile
from pathlib import Path


class AudioPreprocessingError(RuntimeError):
    """Raised when an uploaded audio file cannot be decoded for analysis."""


def convert_to_analysis_wav(audio_path: str | Path, sample_rate: int = 16000) -> str:
    """
    Convert uploaded audio into mono PCM WAV for validators and acoustic models.

    Android records AAC/M4A by default. The transcription backends can often read
    that directly, but soundfile-backed validation and acoustic inference need a
    decoded PCM format.
    """
    source_path = Path(audio_path)
    if not source_path.exists():
        raise AudioPreprocessingError("Audio file not found")

    try:
        import ffmpeg
    except ImportError as exc:
        raise AudioPreprocessingError("Audio conversion dependency is not installed") from exc

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        output_path = temp_file.name

    try:
        (
            ffmpeg
            .input(str(source_path))
            .output(output_path, ac=1, ar=sample_rate, c="pcm_s16le")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except Exception as exc:
        Path(output_path).unlink(missing_ok=True)
        raise AudioPreprocessingError("Invalid or unsupported audio upload") from exc

    return output_path
