from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class EmotionClassifierLoadError(RuntimeError):
    """Raised when the text emotion model cannot be initialized."""


@dataclass
class EmotionClassifierStatus:
    attempted: bool
    loaded: bool
    source: str | None
    source_kind: str | None
    local_model_valid: bool
    local_model_issue: str | None
    failure_reason: str | None


class EmotionClassifier:
    def __init__(self):
        self.model_name = os.getenv("EMOTION_MODEL_NAME", "bhadresh-savani/bert-base-uncased-emotion")
        self.local_model_dir = Path(__file__).with_name("bert_emotion_model")
        self.tokenizer = None
        self.model = None
        self.emotions: dict[int, str] = {}
        self._torch = None
        self._functional = None
        self._load_attempted = False
        self._source: str | None = None
        self._source_kind: str | None = None
        self._failure_reason: str | None = None
        self._local_model_issue: str | None = None
        self._local_model_valid = False

    def _is_lfs_pointer(self, path: Path) -> bool:
        try:
            first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
        except Exception:
            return False
        return first_line.startswith("version https://git-lfs.github.com/spec/v1")

    def _validate_json_file(self, path: Path) -> str | None:
        if not path.exists():
            return f"Missing required file: {path.name}"
        if self._is_lfs_pointer(path):
            return f"{path.name} is a Git LFS pointer, not a real model artifact"
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return f"{path.name} is not valid JSON: {exc}"
        return None

    def _inspect_local_model_dir(self) -> tuple[bool, str | None]:
        if not self.local_model_dir.exists():
            return False, "Local model directory does not exist"

        for filename in ("config.json", "tokenizer_config.json", "special_tokens_map.json"):
            issue = self._validate_json_file(self.local_model_dir / filename)
            if issue:
                return False, issue

        tokenizer_json = self.local_model_dir / "tokenizer.json"
        if tokenizer_json.exists():
            issue = self._validate_json_file(tokenizer_json)
            if issue:
                return False, issue

        vocab_path = self.local_model_dir / "vocab.txt"
        if not vocab_path.exists():
            return False, "Missing required file: vocab.txt"
        if self._is_lfs_pointer(vocab_path):
            return False, "vocab.txt is a Git LFS pointer, not a real model artifact"

        if not any((self.local_model_dir / filename).exists() for filename in ("model.safetensors", "pytorch_model.bin")):
            return False, "Local model directory is missing model weights"

        return True, None

    def _select_model_source(self) -> tuple[str, str]:
        self._local_model_valid, self._local_model_issue = self._inspect_local_model_dir()
        if self._local_model_valid:
            return str(self.local_model_dir), "local"
        return self.model_name, "remote"

    def get_status(self) -> EmotionClassifierStatus:
        return EmotionClassifierStatus(
            attempted=self._load_attempted,
            loaded=self.model is not None,
            source=self._source,
            source_kind=self._source_kind,
            local_model_valid=self._local_model_valid,
            local_model_issue=self._local_model_issue,
            failure_reason=self._failure_reason,
        )

    def _ensure_loaded(self) -> bool:
        if self.model is not None:
            return True
        if self._load_attempted:
            if self._failure_reason:
                raise EmotionClassifierLoadError(self._failure_reason)
            return False

        self._load_attempted = True
        try:
            import torch
            import torch.nn.functional as functional
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            self._failure_reason = f"Emotion model dependencies are not installed: {exc}"
            raise EmotionClassifierLoadError(self._failure_reason) from exc

        model_source, source_kind = self._select_model_source()
        self._source = model_source
        self._source_kind = source_kind

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_source)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_source)
        except Exception as exc:
            self._failure_reason = f"Failed to load {source_kind} emotion model from {model_source}: {exc}"
            raise EmotionClassifierLoadError(self._failure_reason) from exc

        self.model.eval()
        self.emotions = dict(self.model.config.id2label)
        self._torch = torch
        self._functional = functional
        return True

    def predict_emotion(self, text: str) -> dict[str, Any]:
        if not text:
            return {
                "primary_emotion": None,
                "confidence": 0.0,
                "alternative_emotions": [],
                "distribution": {},
            }

        self._ensure_loaded()

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with self._torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = self._functional.softmax(logits, dim=1).squeeze().cpu().numpy()

        distribution = {
            self.emotions[index]: float(probability)
            for index, probability in enumerate(probs.tolist())
        }
        top3_idx = probs.argsort()[-3:][::-1]
        top3_emotions = [self.emotions[i] for i in top3_idx]
        top3_probs = [float(probs[i]) for i in top3_idx]

        return {
            "primary_emotion": top3_emotions[0],
            "confidence": top3_probs[0],
            "label": top3_emotions[0],
            "distribution": distribution,
            "alternative_emotions": [
                {"emotion": emo, "probability": prob}
                for emo, prob in zip(top3_emotions, top3_probs)
            ],
        }


emotion_classifier = EmotionClassifier()
