"""Real-audio sanity checks for the end-to-end mood pipeline.

These checks are intentionally tolerant because speech emotion recognition is noisy on
short real clips. The suite passes if at least 4 of the 5 committed fixtures behave
sensibly end-to-end. Any single miss is reported in the assertion output.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REAL_AUDIO_DIR = Path(__file__).parent / "fixtures" / "real_audio"


FIXTURE_EXPECTATIONS = [
    {
        "filename": "happy_clear.wav",
        "keywords": {"kids", "talking", "door"},
        "top2_label": "happy",
    },
    {
        "filename": "sad_clear.wav",
        "keywords": {"kids", "talking", "door"},
        "top2_label": "sad",
    },
    {
        "filename": "angry_clear.wav",
        "keywords": {"kids", "talking", "door"},
        "top2_label": "angry",
    },
    {
        "filename": "sarcasm.wav",
        "keywords": {"kids", "talking", "door"},
        "sarcasm_case": True,
    },
    {
        "filename": "neutral.wav",
        "keywords": {"kids", "talking", "door"},
        "neutral_case": True,
    },
]


def _post_audio(client, token: str, filename: str):
    file_path = REAL_AUDIO_DIR / filename
    with file_path.open("rb") as audio_file:
        return client.post(
            "/mood/analyze",
            headers={"Authorization": f"Bearer {token}"},
            data={"language": "en"},
            files={"audio_file": (file_path.name, audio_file, "audio/wav")},
        )


@pytest.mark.sanity
def test_real_audio_pipeline_is_sensible_for_at_least_four_of_five_fixtures(client, auth_token, monkeypatch):
    monkeypatch.setenv("FASTER_WHISPER_MODEL", "tiny")
    monkeypatch.setenv("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    failures: list[str] = []

    for expectation in FIXTURE_EXPECTATIONS:
        response = _post_audio(client, auth_token, expectation["filename"])
        assert response.status_code == 200, expectation["filename"]
        payload = response.json()

        transcript = (payload.get("transcript") or "").lower()
        if not transcript.strip():
            failures.append(f"{expectation['filename']}: transcript was empty")
            continue

        if not any(keyword in transcript for keyword in expectation["keywords"]):
            failures.append(
                f"{expectation['filename']}: transcript `{transcript}` did not contain any expected keywords"
            )
            continue

        distribution = payload.get("distribution") or {}
        top2_labels = [
            label
            for label, _probability in sorted(
                distribution.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:2]
        ]

        if expectation.get("top2_label") and expectation["top2_label"] not in top2_labels:
            failures.append(
                f"{expectation['filename']}: expected `{expectation['top2_label']}` in top2, got {top2_labels}"
            )
            continue

        if expectation.get("sarcasm_case"):
            text_label = ((payload.get("text_emotion") or {}).get("label")) or ""
            acoustic_label = ((payload.get("acoustic_emotion") or {}).get("label")) or ""
            if not (payload.get("sarcasm_suspected") or (text_label and acoustic_label and text_label != acoustic_label)):
                failures.append(
                    f"{expectation['filename']}: sarcasm signal missing (text={text_label}, acoustic={acoustic_label})"
                )
                continue

        if expectation.get("neutral_case"):
            non_neutral_max = max(
                (probability for label, probability in distribution.items() if label != "neutral"),
                default=0.0,
            )
            if non_neutral_max >= 0.6:
                failures.append(
                    f"{expectation['filename']}: non-neutral confidence too high ({non_neutral_max:.3f})"
                )
                continue

    assert len(FIXTURE_EXPECTATIONS) - len(failures) >= 4, "\n".join(failures)
