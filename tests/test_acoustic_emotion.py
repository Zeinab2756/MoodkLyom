from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import SHARED_EMOTION_TAXONOMY
from app.services import acoustic_emotion

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class _FakeTensor:
    def __init__(self, values):
        self.values = values

    def to(self, _device):
        return self

    def squeeze(self, _dim=0):
        return self

    def cpu(self):
        return self

    def numpy(self):
        class _Array:
            def __init__(self, values):
                self._values = values

            def tolist(self):
                return self._values

        return _Array(self.values)


class _FakeTorch:
    class _NoGrad:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def no_grad(self):
        return self._NoGrad()

    def softmax(self, _logits, dim=-1):
        return _FakeTensor([0.10, 0.11, 0.12, 0.13, 0.17, 0.14, 0.11, 0.12])


class _FakeFeatureExtractor:
    def __call__(self, waveform, sampling_rate, return_tensors, padding):
        return {
            "input_values": _FakeTensor([waveform]),
            "attention_mask": _FakeTensor([[1] * len(waveform)]),
        }


class _FakeModel:
    def __init__(self):
        self.config = type(
            "Config",
            (),
            {
                "id2label": {
                    0: "angry",
                    1: "calm",
                    2: "disgust",
                    3: "fearful",
                    4: "happy",
                    5: "neutral",
                    6: "sad",
                    7: "surprised",
                }
            },
        )()

    def __call__(self, **_inputs):
        return type("Output", (), {"logits": _FakeTensor([[0.1] * 8])})()


@pytest.fixture
def fake_predictor(monkeypatch):
    predictor = acoustic_emotion.AcousticEmotionPredictor()
    predictor._torch = _FakeTorch()
    predictor._device = "cpu"
    predictor._feature_extractor = None
    predictor.feature_extractor = _FakeFeatureExtractor()
    predictor.model = _FakeModel()
    predictor._load_attempted = True

    import librosa
    import numpy as np
    import soundfile

    predictor._librosa = librosa
    predictor._np = np
    predictor._soundfile = soundfile

    monkeypatch.setattr(predictor, "_ensure_loaded", lambda: None)
    return predictor


def test_predict_acoustic_emotion_returns_taxonomy_distribution_for_sample_wav(fake_predictor):
    result = fake_predictor.predict(FIXTURES_DIR / "mono_2s_16k.wav")

    assert result.label in SHARED_EMOTION_TAXONOMY
    assert set(result.distribution) == set(SHARED_EMOTION_TAXONOMY)
    assert pytest.approx(sum(result.distribution.values()), rel=1e-9, abs=1e-9) == 1.0


def test_predict_acoustic_emotion_raises_clear_error_for_invalid_path():
    with pytest.raises(acoustic_emotion.AcousticEmotionError):
        acoustic_emotion.predict_acoustic_emotion(FIXTURES_DIR / "does_not_exist.wav")


def test_load_audio_resamples_44k_audio_to_16k(fake_predictor):
    waveform = fake_predictor._load_audio(FIXTURES_DIR / "stereo_2s_44k.wav")

    assert len(waveform) in range(31990, 32010)


def test_load_audio_downmixes_stereo_to_mono(fake_predictor):
    waveform = fake_predictor._load_audio(FIXTURES_DIR / "stereo_2s_44k.wav")

    assert waveform.ndim == 1


def test_predict_acoustic_emotion_rejects_corrupt_audio(fake_predictor):
    with pytest.raises(acoustic_emotion.AcousticEmotionError):
        fake_predictor.predict(FIXTURES_DIR / "corrupt_audio.wav")
