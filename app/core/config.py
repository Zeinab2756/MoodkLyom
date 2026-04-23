from __future__ import annotations

import os

SHARED_EMOTION_TAXONOMY = [
    "happy",
    "sad",
    "angry",
    "fearful",
    "surprised",
    "disgusted",
    "neutral",
]

TEXT_EMOTION_LABEL_MAP = {
    "anger": "angry",
    "angry": "angry",
    "calm": "neutral",
    "disgust": "disgusted",
    "disgusted": "disgusted",
    "fear": "fearful",
    "fearful": "fearful",
    "happy": "happy",
    "joy": "happy",
    "love": "happy",
    "neutral": "neutral",
    "sad": "sad",
    "sadness": "sad",
    "surprise": "surprised",
    "surprised": "surprised",
    "anxious": "fearful",
}

ACOUSTIC_EMOTION_LABEL_MAP = {
    "angry": "angry",
    "calm": "neutral",
    "disgust": "disgusted",
    "disgusted": "disgusted",
    "fear": "fearful",
    "fearful": "fearful",
    "happy": "happy",
    "neutral": "neutral",
    "sad": "sad",
    "sadness": "sad",
    "surprise": "surprised",
    "surprised": "surprised",
}

FUSION_AUDIO_WEIGHT = float(os.getenv("FUSION_AUDIO_WEIGHT", "0.6"))
FUSION_TEXT_WEIGHT = float(os.getenv("FUSION_TEXT_WEIGHT", "0.4"))
