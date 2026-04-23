# TEST_REPORT

## Summary

- Static install and startup smoke passed in a fresh virtualenv.
- Functional suite passed: `32 passed` for the default test run.
- Optional performance smoke passed: `1 passed`.
- Targeted AI-pipeline coverage: `94%` total.
- Coverage by critical module:
  - `app/routes/mood_routes.py`: `95%`
  - `app/services/fusion.py`: `95%`
  - `app/services/text_emotion.py`: `93%`
  - `app/services/acoustic_emotion.py`: `93%`

## Layer 1 Results

- `pip install -r requirements.txt` passed in a fresh virtualenv.
- `pip install -r requirements-dev.txt` passed.
- `uvicorn app.main:app` started successfully.
- Health-equivalent smoke passed with `GET /` returning `200`.
- Import audit passed for:
  - `app.services.text_emotion`
  - `app.services.acoustic_emotion`
  - `app.services.fusion`
  - `app.routes.mood_routes`
- Router registration check passed for:
  - `/voice/transcribe`
  - `/emotion/analyze`
  - `/emotion/health`
  - `/mood/analyze`
- `mypy app/` was not run because `mypy` is not part of the repo's existing toolchain or installed dev dependencies.
- `ruff check app/` reported style-only issues during the first pass. Those do not block functional validation and were handled separately at the end.

## Layer 2 and 3 Results

- Unit tests passed for fusion, text-emotion fallback behavior, and acoustic preprocessing/error handling.
- Integration tests passed for:
  - `/mood/analyze` schema and graceful degradation
  - parallel execution wiring
  - invalid upload handling
  - oversized upload rejection
  - `/voice/transcribe` regression coverage
  - `/emotion/health` regression coverage
  - `/emotion/analyze` routing through the new text-emotion facade

## Real-Audio Sanity

All `5/5` committed fixtures passed the sanity threshold.

- `happy_clear.wav`: fused top-2 included `happy`
- `sad_clear.wav`: fused top-2 included `sad`
- `angry_clear.wav`: fused top-2 included `angry`
- `sarcasm.wav`: sarcasm signal detected through branch disagreement
- `neutral.wav`: no non-neutral label exceeded `0.6`

Notes:

- The committed RAVDESS fixtures use neutral spoken text with emotional delivery. As a result, the text branch often predicts `neutral` while the acoustic branch carries the emotional signal.
- That behavior is acceptable for these sanity tests because the product goal is multimodal mood detection, not transcript sentiment alone.

## Performance Smoke

Results from `pytest -m slow tests/test_performance.py -q`:

- Cold-start latency: `40.001s`
- Warm-call p50: `1.817s`
- Warm-call p95: `1.842s`
- RSS before model load: `4521984` bytes
- RSS after model load: `4509696` bytes

Notes:

- The cold-start number is dominated by first-load model initialization on CPU.
- The warm-call latency is within the requested `p95 < 3s` target for short test audio on CPU.
- The Windows RSS numbers are unexpectedly low and should be treated as approximate smoke metrics rather than precise capacity-planning numbers.

## AI Defects Found and Fixed

- `fix(acoustic): load wav2vec2 classifier weights correctly`
  - The acoustic branch was loading the model architecture in a way that left the classifier head effectively unusable on real audio.
  - Fixed by loading the published `safetensors` checkpoint explicitly and remapping the classifier keys to the current `transformers` module layout.
- `fix(ai): normalize acoustic outputs and single-modality fusion handling`
  - Empty or missing modality outputs could be treated like a real neutral distribution.
  - Fixed so missing branches are treated as unavailable, single-modality fusion is warned, and confidence is capped.
- `fix(api): validate mood uploads and declare multipart runtime dependency`
  - `/mood/analyze` now rejects invalid audio with `400`, missing files with `422`, and oversized uploads with `413`.
- `fix(transcription): enable offline ASR via faster-whisper fallback`
  - Preserved a usable local transcription path in clean Python 3.13 installs where `openai-whisper` is not viable.

## Open Items

- `ruff` findings were style-level only; they do not change runtime behavior. They were cleaned up separately after functional validation.
- The upstream acoustic model emits a `transformers` deprecation warning related to `gradient_checkpointing` in the published config.
- Cold start is high on CPU and would benefit from model warm-up or a preload strategy before production rollout.
- `mypy` is still not part of the repo's standard toolchain.
