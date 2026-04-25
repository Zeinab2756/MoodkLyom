from __future__ import annotations

import tempfile
import subprocess
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

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        output_path = temp_file.name

    try:
        _convert_with_ffmpeg_python(source_path, output_path, sample_rate)
    except Exception:
        try:
            _convert_with_ffmpeg_cli(source_path, output_path, sample_rate)
        except Exception as cli_exc:
            Path(output_path).unlink(missing_ok=True)
            raise AudioPreprocessingError(
                "Audio conversion failed. Install ffmpeg-python or make sure ffmpeg is available on PATH."
            ) from cli_exc

    return output_path


def _convert_with_ffmpeg_python(source_path: Path, output_path: str, sample_rate: int) -> None:
    import ffmpeg

    (
        ffmpeg
        .input(str(source_path))
        .output(output_path, ac=1, ar=sample_rate, c="pcm_s16le")
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )


def _convert_with_ffmpeg_cli(source_path: Path, output_path: str, sample_rate: int) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-c:a",
            "pcm_s16le",
            output_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
