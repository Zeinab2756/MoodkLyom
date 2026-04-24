import json

from app.models.emotion_model import EmotionClassifier


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_local_model_dir_is_rejected_when_files_are_lfs_pointers(tmp_path):
    classifier = EmotionClassifier()
    classifier.local_model_dir = tmp_path

    for filename in ("config.json", "tokenizer_config.json", "special_tokens_map.json", "tokenizer.json", "vocab.txt"):
        (tmp_path / filename).write_text(
            "version https://git-lfs.github.com/spec/v1\noid sha256:test\nsize 123\n",
            encoding="utf-8",
        )

    valid, issue = classifier._inspect_local_model_dir()

    assert valid is False
    assert "Git LFS pointer" in issue


def test_select_model_source_falls_back_to_remote_when_local_model_is_invalid(tmp_path):
    classifier = EmotionClassifier()
    classifier.local_model_dir = tmp_path
    classifier.model_name = "remote/model"

    _write_json(tmp_path / "config.json", {"model_type": "bert"})
    _write_json(tmp_path / "tokenizer_config.json", {"do_lower_case": True})
    _write_json(tmp_path / "special_tokens_map.json", {"unk_token": "[UNK]"})
    (tmp_path / "vocab.txt").write_text("[PAD]\n[UNK]\n", encoding="utf-8")

    source, source_kind = classifier._select_model_source()

    assert source == "remote/model"
    assert source_kind == "remote"
    assert classifier._local_model_valid is False
    assert classifier._local_model_issue == "Local model directory is missing model weights"


def test_select_model_source_prefers_local_when_required_files_exist(tmp_path):
    classifier = EmotionClassifier()
    classifier.local_model_dir = tmp_path

    _write_json(tmp_path / "config.json", {"model_type": "bert"})
    _write_json(tmp_path / "tokenizer_config.json", {"do_lower_case": True})
    _write_json(tmp_path / "special_tokens_map.json", {"unk_token": "[UNK]"})
    _write_json(tmp_path / "tokenizer.json", {"version": "1.0", "truncation": None})
    (tmp_path / "vocab.txt").write_text("[PAD]\n[UNK]\n", encoding="utf-8")
    (tmp_path / "model.safetensors").write_bytes(b"placeholder")

    source, source_kind = classifier._select_model_source()

    assert source == str(tmp_path)
    assert source_kind == "local"
    assert classifier._local_model_valid is True
    assert classifier._local_model_issue is None
