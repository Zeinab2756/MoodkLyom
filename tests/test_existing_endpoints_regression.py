from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_voice_transcribe_response_shape_matches_android_contract(client, auth_token, monkeypatch):
    monkeypatch.setattr(
        "app.routes.voice.transcribe_audio_file",
        lambda path, language=None: (True, "voice works", None),
    )

    with (FIXTURES_DIR / "happy_short.wav").open("rb") as audio_file:
        response = client.post(
            "/voice/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"audio_file": ("happy_short.wav", audio_file, "audio/wav")},
        )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "text": "voice works",
        "message": None,
    }


def test_emotion_health_returns_expected_shape(client, monkeypatch):
    async def fake_predict(_text: str):
        return type(
            "FakeEmotion",
            (),
            {
                "model_dump": lambda self: {
                    "label": "happy",
                    "confidence": 0.8,
                    "distribution": {"happy": 0.8, "neutral": 0.2},
                    "source": "bert",
                }
            },
        )()

    monkeypatch.setattr("app.routes.emotion_routes.predict_text_emotion_async", fake_predict)

    response = client.get("/emotion/health")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"status", "sample_text", "prediction"}
    assert payload["status"] == "ok"


def test_emotion_analyze_uses_new_facade_underneath(client, monkeypatch):
    calls = {"bert": 0}

    def fake_bert(_text: str):
        calls["bert"] += 1
        return {
            "primary_emotion": "joy",
            "confidence": 0.91,
            "distribution": {"joy": 0.91, "surprise": 0.09},
        }

    monkeypatch.setattr("app.services.text_emotion.emotion_classifier.predict_emotion", fake_bert)

    response = client.post("/emotion/analyze", json={"text": "I am happy"})

    assert response.status_code == 200
    assert calls["bert"] == 1
    payload = response.json()
    assert payload["primary_emotion"] == "joy"
    assert "alternative_emotions" in payload
