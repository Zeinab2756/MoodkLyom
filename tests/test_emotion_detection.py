import asyncio

from app.services import emotion_detection


def test_external_emotion_requires_explicit_url(monkeypatch):
    monkeypatch.setattr(emotion_detection, "EMOTION_API_URL", "")

    async def run():
        try:
            await emotion_detection.predict_external_emotion("hello")
        except Exception as exc:
            return exc
        raise AssertionError("expected an exception")

    error = asyncio.run(run())

    assert isinstance(error, NotImplementedError)
    assert str(error) == "EMOTION_API_URL is not configured"
