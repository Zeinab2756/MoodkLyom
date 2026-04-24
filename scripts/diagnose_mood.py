from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import warnings
from pathlib import Path

import soundfile

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings(
    "ignore",
    message=r"Passing `gradient_checkpointing` to a config initialization is deprecated.*",
    category=UserWarning,
)

from app.core.config import (  # noqa: E402
    ACOUSTIC_EMOTION_LABEL_MAP,
    FUSION_AUDIO_WEIGHT,
    FUSION_TEXT_WEIGHT,
    TEXT_EMOTION_LABEL_MAP,
)
from app.models.emotion_model import emotion_classifier  # noqa: E402
from app.schemas.emotion_schemas import EmotionDistribution  # noqa: E402
from app.services.acoustic_emotion import acoustic_emotion_predictor  # noqa: E402
from app.services.fusion import fuse  # noqa: E402
from app.services.text_emotion import predict_text_emotion_with_diagnostics  # noqa: E402
from app.services.transcription import (  # noqa: E402
    _load_faster_whisper_model,
    _load_local_whisper_model,
    _transcribe_with_azure_openai,
    _transcribe_with_openai,
)

LINE_WIDTH = 60
BAR_WIDTH = 20


def _heading(title: str) -> str:
    line = "═" * LINE_WIDTH
    return f"{line}\n  {title}\n{line}"


def _section(title: str) -> str:
    return f"  ── {title} " + "─" * max(1, LINE_WIDTH - len(title) - 7)


def _bar(probability: float) -> str:
    filled = max(0, min(BAR_WIDTH, int(round(probability * BAR_WIDTH))))
    return ("█" * filled) + ("░" * (BAR_WIDTH - filled))


def _format_top3(items: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for item in items[:3]:
        native = str(item["native"])
        mapped = str(item["mapped"])
        probability = float(item["probability"])
        label = native if native == mapped else f"{native} -> {mapped}"
        lines.append(f"    {label:<23}{_bar(probability)}  {probability:.2f}")
    return lines


def _normalized_distribution(distribution: dict[str, float]) -> dict[str, float]:
    cleaned = {
        label: max(float(probability), 0.0)
        for label, probability in distribution.items()
    }
    total = sum(cleaned.values())
    if total <= 0:
        return {}
    return {
        label: probability / total
        for label, probability in cleaned.items()
    }


def _top_items(distribution: dict[str, float], label_map: dict[str, str]) -> list[dict[str, object]]:
    sorted_items = sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:3]
    return [
        {
            "native": label,
            "mapped": label_map.get(label.strip().lower(), label.strip().lower()),
            "probability": float(probability),
        }
        for label, probability in sorted_items
    ]


def _inspect_audio(audio_path: Path) -> dict[str, object]:
    info = soundfile.info(str(audio_path))
    processed_sample_rate = acoustic_emotion_predictor.target_sample_rate
    processed_channels = 1
    duration_seconds = float(info.frames / info.samplerate) if info.samplerate else 0.0
    processed_frames = int(round(duration_seconds * processed_sample_rate))

    return {
        "duration_seconds": duration_seconds,
        "sample_rate_hz": int(info.samplerate),
        "processed_sample_rate_hz": int(processed_sample_rate),
        "channels": int(info.channels),
        "processed_channels": processed_channels,
        "frames": int(info.frames),
        "processed_frames": processed_frames,
        "resampled": int(info.samplerate) != int(processed_sample_rate),
        "downmixed": int(info.channels) != processed_channels,
    }


def _transcribe(audio_path: Path, language: str | None) -> dict[str, object]:
    started = time.perf_counter()

    openai_text = _transcribe_with_openai(audio_path, language)
    if openai_text:
        return {
            "backend": "openai",
            "language": language,
            "language_confidence": None,
            "text": openai_text,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "warning": None,
        }

    azure_text = _transcribe_with_azure_openai(audio_path, language)
    if azure_text:
        return {
            "backend": "azure-openai",
            "language": language,
            "language_confidence": None,
            "text": azure_text,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "warning": None,
        }

    faster_model = _load_faster_whisper_model()
    if faster_model is not None:
        segments, info = faster_model.transcribe(str(audio_path), language=language or None)
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        if text:
            return {
                "backend": "faster-whisper (local)",
                "language": getattr(info, "language", language),
                "language_confidence": getattr(info, "language_probability", None),
                "text": text,
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "warning": None,
            }

    whisper_model = _load_local_whisper_model()
    if whisper_model is not None:
        result = whisper_model.transcribe(str(audio_path), language=language or None)
        text = (result.get("text") or "").strip()
        if text:
            return {
                "backend": "whisper (local)",
                "language": result.get("language", language),
                "language_confidence": None,
                "text": text,
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "warning": None,
            }

    fallback_text = os.getenv("TRANSCRIPTION_FALLBACK_TEXT")
    if fallback_text:
        return {
            "backend": "env-fallback",
            "language": language,
            "language_confidence": None,
            "text": fallback_text,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "warning": "Transcription backend is not configured",
        }

    return {
        "backend": "unavailable",
        "language": language,
        "language_confidence": None,
        "text": None,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "warning": "Transcription backend is not configured",
    }


def _diagnose_text_emotion(text: str) -> dict[str, object]:
    started = time.perf_counter()
    emotion, diagnostics = asyncio.run(predict_text_emotion_with_diagnostics(text))
    status = emotion_classifier.get_status()
    native_distribution = diagnostics.bert.distribution if diagnostics.selected_source == "bert" else emotion.distribution
    return {
        "backend": {
            "external": "external emotion API",
            "keyword": "keyword fallback",
            "bert": "BERT classifier",
            "empty": "empty input",
        }.get(emotion.source, emotion.source),
        "source": emotion.source,
        "emotion": emotion,
        "native_distribution": native_distribution,
        "top3": _top_items(native_distribution, TEXT_EMOTION_LABEL_MAP),
        "diagnostics": {
            "selected_source": diagnostics.selected_source,
            "bert": diagnostics.bert.__dict__,
            "external": diagnostics.external.__dict__,
            "keyword": diagnostics.keyword.__dict__,
            "model_status": status.__dict__,
        },
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }


def _diagnose_acoustic_emotion(audio_path: Path) -> dict[str, object]:
    started = time.perf_counter()
    acoustic_emotion_predictor._ensure_loaded()
    waveform = acoustic_emotion_predictor._load_audio(audio_path)
    inputs = acoustic_emotion_predictor.feature_extractor(
        waveform,
        sampling_rate=acoustic_emotion_predictor.target_sample_rate,
        return_tensors="pt",
        padding=True,
    )
    inputs = {
        name: value.to(acoustic_emotion_predictor._device)
        for name, value in inputs.items()
    }
    with acoustic_emotion_predictor._torch.no_grad():
        logits = acoustic_emotion_predictor.model(**inputs).logits
        probabilities = acoustic_emotion_predictor._torch.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

    raw_distribution = {
        str(acoustic_emotion_predictor.model.config.id2label[index]).strip().lower(): float(probability)
        for index, probability in enumerate(probabilities.tolist())
    }
    mapped_distribution = acoustic_emotion_predictor._normalize_distribution(raw_distribution)
    label, confidence = max(mapped_distribution.items(), key=lambda item: item[1])
    emotion = EmotionDistribution(
        label=label,
        confidence=confidence,
        distribution=mapped_distribution,
        source="acoustic",
    )
    return {
        "backend": acoustic_emotion_predictor.model_name,
        "device": acoustic_emotion_predictor._device,
        "emotion": emotion,
        "native_distribution": raw_distribution,
        "top3": _top_items(raw_distribution, ACOUSTIC_EMOTION_LABEL_MAP),
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }


def _render_console(result: dict[str, object]) -> str:
    audio = result["audio"]
    lines = [
        _heading("Mood Pipeline Diagnostic"),
        f"  File:         {result['file']}",
        (
            f"  Duration:     {audio['duration_seconds']:.1f}s | "
            f"Sample rate: {audio['sample_rate_hz']} Hz"
            + (
                f" -> resampled to {audio['processed_sample_rate_hz']} Hz"
                if audio["resampled"]
                else ""
            )
        ),
        (
            f"  Channels:     {audio['channels']}"
            + (" (stereo)" if audio["channels"] == 2 else " (mono)")
            + (
                " -> downmixed to mono"
                if audio["downmixed"]
                else ""
            )
        ),
        "",
    ]

    transcription = result.get("transcription")
    if transcription:
        language_confidence = transcription.get("language_confidence")
        language_line = str(transcription.get("language") or "unknown")
        if language_confidence is not None:
            language_line += f" (confidence {float(language_confidence):.2f})"
        lines.extend(
            [
                _section("TRANSCRIPTION"),
                f"  Backend:      {transcription['backend']}",
                f"  Language:     {language_line}",
                f'  Text:         "{transcription.get("text") or ""}"',
                f"  Took:         {transcription['elapsed_ms']} ms",
            ]
        )
        if transcription.get("warning"):
            lines.append(f"  Warning:      {transcription['warning']}")
        lines.append("")

    text = result.get("text_emotion")
    if text:
        diagnostics = text.get("diagnostics", {})
        model_status = diagnostics.get("model_status", {})
        bert_attempt = diagnostics.get("bert", {})
        lines.extend(
            [
                _section("TEXT EMOTION (BERT FACADE)"),
                f"  Primary backend: {text['backend']}",
                f"  BERT attempted: {('yes' if bert_attempt.get('attempted') else 'no')}",
                f"  BERT load:      {('success' if model_status.get('loaded') else 'failure')}",
                (
                    f"  BERT source:    {model_status.get('source_kind')} -> {model_status.get('source')}"
                    if model_status.get("source")
                    else "  BERT source:    unavailable"
                ),
                "  Top 3:",
                *_format_top3(text["top3"]),
                f"  Took:         {text['elapsed_ms']} ms",
                "",
            ]
        )
        if model_status.get("local_model_issue"):
            lines.append(f"  Local model:    {model_status['local_model_issue']}")
        if bert_attempt.get("reason"):
            lines.append(f"  BERT fallback:  {bert_attempt['reason']}")
        external_attempt = diagnostics.get("external", {})
        if external_attempt.get("reason"):
            lines.append(f"  External miss:  {external_attempt['reason']}")
        lines.append("")

    acoustic = result.get("acoustic_emotion")
    if acoustic:
        lines.extend(
            [
                _section("ACOUSTIC EMOTION (WAV2VEC2)"),
                f"  Model:        {acoustic['backend']}",
                f"  Device:       {acoustic['device']}",
                "  Top 3:",
                *_format_top3(acoustic["top3"]),
                f"  Took:         {acoustic['elapsed_ms']} ms",
                "",
            ]
        )

    fusion_result = result.get("fusion")
    if fusion_result:
        text_top = text["top3"][0] if text and text["top3"] else None
        audio_top = acoustic["top3"][0] if acoustic and acoustic["top3"] else None
        lines.extend(
            [
                _section("FUSION"),
                f"  Weights:           w_audio={fusion_result['weights']['audio']:.2f}, "
                f"w_text={fusion_result['weights']['text']:.2f}",
            ]
        )
        if text_top:
            lines.append(
                f"  Mapped text top:   {text_top['mapped']}  "
                f'(native "{text_top["native"]}" -> taxonomy "{text_top["mapped"]}")'
            )
        if audio_top:
            lines.append(
                f"  Mapped audio top:  {audio_top['mapped']}  "
                f'(native "{audio_top["native"]}" -> taxonomy "{audio_top["mapped"]}")'
            )
        lines.extend(["", "  Fused distribution:"])
        fused_top = sorted(
            fusion_result["distribution"].items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]
        for label, probability in fused_top:
            lines.append(f"    {label:<12}{_bar(float(probability))}  {float(probability):.2f}")
        lines.extend(
            [
                "",
                f"  Final mood:        {fusion_result['label']} "
                f"(confidence {fusion_result['confidence']:.2f})",
                f"  Sarcasm suspected: {'YES' if fusion_result['sarcasm_suspected'] else 'NO'}",
            ]
        )
        if fusion_result["sarcasm_suspected"] and text_top and audio_top:
            lines.append(
                f"                     text says {text_top['mapped']} ({text_top['probability']:.2f}) "
                f"but tone says {audio_top['mapped']} ({audio_top['probability']:.2f})"
            )
        if fusion_result.get("warnings"):
            for warning in fusion_result["warnings"]:
                lines.append(f"  Warning:          {warning}")
        lines.extend(["", f"  Total pipeline:    {result['total_elapsed_ms'] / 1000:.2f} s", "═" * LINE_WIDTH])

    return "\n".join(lines)


def run_diagnostic(
    audio_path: Path,
    *,
    language: str | None,
    w_audio: float,
    w_text: float,
    audio_only: bool,
    text_only: bool,
) -> dict[str, object]:
    started = time.perf_counter()
    audio_info = _inspect_audio(audio_path)
    result: dict[str, object] = {
        "file": str(audio_path),
        "audio": audio_info,
        "warnings": [],
    }

    transcription = None
    text_emotion = None
    acoustic_emotion = None

    if not audio_only:
        transcription = _transcribe(audio_path, language)
        result["transcription"] = transcription

        text_value = transcription.get("text") if transcription else None
        if text_value and not text_only:
            text_emotion = _diagnose_text_emotion(str(text_value))
            result["text_emotion"] = {
                **text_emotion,
                "emotion": text_emotion["emotion"].model_dump(),
            }
        elif text_value and text_only:
            text_emotion = _diagnose_text_emotion(str(text_value))
            result["text_emotion"] = {
                **text_emotion,
                "emotion": text_emotion["emotion"].model_dump(),
            }
        else:
            result["warnings"].append("Text emotion skipped because transcription did not produce text")

    if not text_only:
        acoustic_emotion = _diagnose_acoustic_emotion(audio_path)
        result["acoustic_emotion"] = {
            **acoustic_emotion,
            "emotion": acoustic_emotion["emotion"].model_dump(),
        }

    fused = fuse(
        acoustic_emotion["emotion"] if acoustic_emotion else None,
        text_emotion["emotion"] if text_emotion else None,
        w_audio=w_audio,
        w_text=w_text,
    )
    result["fusion"] = {
        **fused.model_dump(),
        "weights": {"audio": w_audio, "text": w_text},
    }
    result["total_elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return result


def _parse_weights(raw: str) -> tuple[float, float]:
    try:
        audio_raw, text_raw = [item.strip() for item in raw.split(",", 1)]
        return float(audio_raw), float(text_raw)
    except Exception as exc:
        raise argparse.ArgumentTypeError("Weights must be in the form w_audio,w_text") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose the multimodal mood pipeline for a single audio file.")
    parser.add_argument("audio_path", type=Path)
    parser.add_argument("--language", default="en")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--weights", type=_parse_weights, default=(FUSION_AUDIO_WEIGHT, FUSION_TEXT_WEIGHT))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--audio-only", action="store_true")
    group.add_argument("--text-only", action="store_true")
    args = parser.parse_args()

    audio_path = args.audio_path.resolve()
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    result = run_diagnostic(
        audio_path,
        language=args.language,
        w_audio=args.weights[0],
        w_text=args.weights[1],
        audio_only=args.audio_only,
        text_only=args.text_only,
    )

    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_render_console(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
