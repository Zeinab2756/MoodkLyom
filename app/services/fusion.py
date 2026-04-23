from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.config import (
    ACOUSTIC_EMOTION_LABEL_MAP,
    FUSION_AUDIO_WEIGHT,
    FUSION_TEXT_WEIGHT,
    SHARED_EMOTION_TAXONOMY,
    TEXT_EMOTION_LABEL_MAP,
)
from app.schemas.emotion_schemas import EmotionDistribution


class FusedMood(BaseModel):
    label: str
    confidence: float
    distribution: dict[str, float] = Field(default_factory=dict)
    sarcasm_suspected: bool = False


def _normalize_distribution(distribution: dict[str, float]) -> dict[str, float]:
    sanitized = {
        label: max(float(probability), 0.0)
        for label, probability in distribution.items()
    }
    total = sum(sanitized.values())
    if total <= 0:
        return {}
    return {
        label: probability / total
        for label, probability in sanitized.items()
    }


def _project_distribution(
    emotion: EmotionDistribution | None,
    label_map: dict[str, str],
) -> dict[str, float]:
    projected = {label: 0.0 for label in SHARED_EMOTION_TAXONOMY}
    if emotion is None:
        return {}

    raw_distribution = emotion.distribution or {}
    if not raw_distribution and emotion.label:
        raw_distribution = {emotion.label: emotion.confidence or 1.0}

    for raw_label, probability in raw_distribution.items():
        normalized_label = label_map.get(raw_label.strip().lower())
        if not normalized_label:
            continue
        projected[normalized_label] += max(float(probability), 0.0)

    return _normalize_distribution(projected)


def _top_label(distribution: dict[str, float]) -> tuple[str, float]:
    if not distribution:
        return "neutral", 0.0
    return max(distribution.items(), key=lambda item: item[1])


def fuse(
    acoustic_dist: EmotionDistribution | None,
    text_dist: EmotionDistribution | None,
    w_audio: float = FUSION_AUDIO_WEIGHT,
    w_text: float = FUSION_TEXT_WEIGHT,
) -> FusedMood:
    acoustic_shared = _project_distribution(acoustic_dist, ACOUSTIC_EMOTION_LABEL_MAP)
    text_shared = _project_distribution(text_dist, TEXT_EMOTION_LABEL_MAP)

    audio_available = bool(acoustic_shared)
    text_available = bool(text_shared)

    if not audio_available and not text_available:
        return FusedMood(
            label="neutral",
            confidence=0.0,
            distribution={label: 0.0 for label in SHARED_EMOTION_TAXONOMY},
            sarcasm_suspected=False,
        )

    if audio_available and text_available:
        total_weight = max(w_audio, 0.0) + max(w_text, 0.0)
        audio_weight = max(w_audio, 0.0) / total_weight if total_weight else 0.5
        text_weight = max(w_text, 0.0) / total_weight if total_weight else 0.5
    elif audio_available:
        audio_weight = 1.0
        text_weight = 0.0
    else:
        audio_weight = 0.0
        text_weight = 1.0

    fused_distribution = {
        label: (acoustic_shared.get(label, 0.0) * audio_weight)
        + (text_shared.get(label, 0.0) * text_weight)
        for label in SHARED_EMOTION_TAXONOMY
    }
    fused_distribution = _normalize_distribution(fused_distribution)

    fused_label, fused_confidence = _top_label(fused_distribution)
    audio_label, audio_confidence = _top_label(acoustic_shared)
    text_label, text_confidence = _top_label(text_shared)

    sarcasm_suspected = (
        audio_available
        and text_available
        and audio_label != text_label
        and audio_confidence > 0.6
        and text_confidence > 0.6
    )

    return FusedMood(
        label=fused_label,
        confidence=fused_confidence,
        distribution=fused_distribution,
        sarcasm_suspected=sarcasm_suspected,
    )
