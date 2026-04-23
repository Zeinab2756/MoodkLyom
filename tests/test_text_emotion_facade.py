import asyncio

from app.services import text_emotion


def test_facade_returns_bert_result_when_available(monkeypatch):
    monkeypatch.setattr(
        text_emotion.emotion_classifier,
        "predict_emotion",
        lambda text: {
            "primary_emotion": "joy",
            "confidence": 0.9,
            "distribution": {"joy": 0.9, "surprise": 0.1},
        },
    )

    result = asyncio.run(text_emotion.predict_text_emotion_async("great day"))

    assert result.label == "joy"
    assert result.source == "bert"


def test_facade_falls_through_to_external_api_when_bert_raises(monkeypatch):
    def raise_from_bert(_text):
        raise RuntimeError("bert unavailable")

    async def external_result(_text):
        return {
            "emotion": "sad",
            "confidence": 0.75,
            "distribution": {"sad": 0.75, "neutral": 0.25},
        }

    monkeypatch.setattr(text_emotion.emotion_classifier, "predict_emotion", raise_from_bert)
    monkeypatch.setattr(text_emotion, "predict_external_emotion", external_result)

    result = asyncio.run(text_emotion.predict_text_emotion_async("not great"))

    assert result.label == "sad"
    assert result.source == "external"


def test_facade_falls_through_to_keyword_detection_when_bert_and_external_raise(monkeypatch):
    def raise_from_bert(_text):
        raise RuntimeError("bert unavailable")

    async def raise_from_external(_text):
        raise RuntimeError("external unavailable")

    monkeypatch.setattr(text_emotion.emotion_classifier, "predict_emotion", raise_from_bert)
    monkeypatch.setattr(text_emotion, "predict_external_emotion", raise_from_external)
    monkeypatch.setattr(
        text_emotion,
        "predict_keyword_emotion",
        lambda text: {
            "emotion": "anxious",
            "confidence": 0.6,
            "distribution": {"anxious": 0.6, "neutral": 0.4},
        },
    )

    result = asyncio.run(text_emotion.predict_text_emotion_async("I am worried"))

    assert result.label == "anxious"
    assert result.source == "keyword"


def test_facade_returns_neutral_for_empty_input():
    result = asyncio.run(text_emotion.predict_text_emotion_async("   "))

    assert result.label == "neutral"
    assert result.confidence == 0.0
    assert result.distribution == {}


def test_facade_handles_very_long_text_without_crashing(monkeypatch):
    seen = {}

    def fake_bert(text):
        seen["length"] = len(text)
        return {
            "primary_emotion": "joy",
            "confidence": 0.8,
            "distribution": {"joy": 0.8, "surprise": 0.2},
        }

    monkeypatch.setattr(text_emotion.emotion_classifier, "predict_emotion", fake_bert)

    result = asyncio.run(text_emotion.predict_text_emotion_async("happy " * 1200))

    assert result.label == "joy"
    assert seen["length"] > 5000


def test_to_emotion_distribution_normalizes_alternative_shapes():
    result = text_emotion._to_emotion_distribution(
        {
            "alternative_emotions": [
                {"emotion": "Joy", "probability": 2},
                {"emotion": "Surprise", "probability": 1},
            ]
        },
        source="external",
    )

    assert result.label == "joy"
    assert result.distribution["joy"] == 2 / 3


def test_sync_wrapper_runs_outside_event_loop(monkeypatch):
    monkeypatch.setattr(
        text_emotion.emotion_classifier,
        "predict_emotion",
        lambda text: {
            "primary_emotion": "joy",
            "confidence": 0.8,
            "distribution": {"joy": 0.8, "surprise": 0.2},
        },
    )

    result = text_emotion.predict_text_emotion("works")

    assert result.label == "joy"
    assert result.source == "bert"
