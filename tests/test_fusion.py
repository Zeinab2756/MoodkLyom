import math

from app.schemas.emotion_schemas import EmotionDistribution
from app.services.fusion import fuse


def test_fuse_agreement_case_prefers_happy_without_sarcasm():
    acoustic = EmotionDistribution(
        label="happy",
        confidence=0.8,
        distribution={"happy": 0.8, "neutral": 0.2},
        source="acoustic",
    )
    text = EmotionDistribution(
        label="happy",
        confidence=0.7,
        distribution={"happy": 0.7, "surprised": 0.3},
        source="bert",
    )

    fused = fuse(acoustic, text)

    assert fused.label == "happy"
    assert fused.confidence > 0.7
    assert fused.sarcasm_suspected is False


def test_fuse_disagreement_case_flags_sarcasm_and_follows_weighted_signal():
    acoustic = EmotionDistribution(
        label="sad",
        confidence=0.75,
        distribution={"sad": 0.75, "neutral": 0.25},
        source="acoustic",
    )
    text = EmotionDistribution(
        label="happy",
        confidence=0.7,
        distribution={"happy": 0.7, "neutral": 0.3},
        source="bert",
    )

    fused = fuse(acoustic, text)

    assert fused.label == "sad"
    assert fused.sarcasm_suspected is True


def test_fuse_low_confidence_disagreement_does_not_flag_sarcasm():
    acoustic = EmotionDistribution(
        label="sad",
        confidence=0.35,
        distribution={"sad": 0.35, "neutral": 0.65},
        source="acoustic",
    )
    text = EmotionDistribution(
        label="happy",
        confidence=0.30,
        distribution={"happy": 0.30, "neutral": 0.70},
        source="bert",
    )

    fused = fuse(acoustic, text)

    assert fused.sarcasm_suspected is False
    assert fused.label == "neutral"


def test_fuse_single_modality_returns_acoustic_only_result_with_warning():
    acoustic = EmotionDistribution(
        label="fearful",
        confidence=0.86,
        distribution={"fearful": 0.86, "neutral": 0.14},
        source="acoustic",
    )
    text = EmotionDistribution(label="neutral", confidence=0.0, distribution={}, source="empty")

    fused = fuse(acoustic, text)

    assert fused.label == "fearful"
    assert fused.confidence < acoustic.confidence
    assert any("single" in warning.lower() or "modality" in warning.lower() for warning in fused.warnings)


def test_fuse_maps_native_bert_labels_to_shared_taxonomy():
    text = EmotionDistribution(
        label="joy",
        confidence=0.9,
        distribution={"joy": 0.6, "love": 0.25, "surprise": 0.15},
        source="bert",
    )

    fused = fuse(None, text)

    assert fused.label == "happy"
    assert "happy" in fused.distribution
    assert "surprised" in fused.distribution


def test_fuse_maps_native_wav2vec_labels_to_shared_taxonomy():
    acoustic = EmotionDistribution(
        label="calm",
        confidence=0.8,
        distribution={"calm": 0.8, "surprised": 0.2},
        source="acoustic",
    )

    fused = fuse(acoustic, None)

    assert fused.label == "neutral"
    assert fused.distribution["neutral"] > 0.7


def test_fuse_respects_weight_override():
    acoustic = EmotionDistribution(
        label="sad",
        confidence=0.7,
        distribution={"sad": 0.7, "neutral": 0.3},
        source="acoustic",
    )
    text = EmotionDistribution(
        label="happy",
        confidence=0.85,
        distribution={"happy": 0.85, "neutral": 0.15},
        source="bert",
    )

    fused = fuse(acoustic, text, w_audio=0.9, w_text=0.1)

    assert fused.label == "sad"


def test_fused_distribution_sums_to_one():
    acoustic = EmotionDistribution(
        label="angry",
        confidence=0.55,
        distribution={"angry": 0.55, "neutral": 0.45},
        source="acoustic",
    )
    text = EmotionDistribution(
        label="surprised",
        confidence=0.65,
        distribution={"surprised": 0.65, "neutral": 0.35},
        source="bert",
    )

    fused = fuse(acoustic, text)

    assert math.isclose(sum(fused.distribution.values()), 1.0, rel_tol=1e-9, abs_tol=1e-9)
