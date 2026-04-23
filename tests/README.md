# Test Layers

This repo validates the mood AI pipeline in five layers:

1. `Layer 1: static checks`
   - Clean install in a fresh virtualenv.
   - `uvicorn app.main:app` startup smoke.
   - Import audit for the AI service modules and `/mood/analyze` route.
   - Router registration checks for `/voice/transcribe`, `/emotion/analyze`, `/emotion/health`, and `/mood/analyze`.
   - `ruff check app/` and optional `mypy app/`.
2. `Layer 2: unit tests`
   - `tests/test_fusion.py`
   - `tests/test_text_emotion_facade.py`
   - `tests/test_acoustic_emotion.py`
3. `Layer 3: integration tests`
   - `tests/test_mood_endpoint.py`
   - `tests/test_existing_endpoints_regression.py`
4. `Layer 4: real-audio sanity`
   - `tests/test_real_audio_sanity.py`
   - Runs the full `/mood/analyze` pipeline against committed short WAV fixtures.
   - The test is intentionally tolerant and passes when at least 4 of 5 fixtures behave sensibly.
5. `Layer 5: performance smoke`
   - `tests/test_performance.py`
   - Marked `slow`.
   - Starts a local uvicorn process, measures cold start plus 10 warm calls, and writes `performance_report.md`.

# Running Tests

Create or reuse the project virtualenv, then install both dependency files:

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run the normal test suite:

```powershell
pytest -m "not slow"
```

Run only the real-audio sanity layer:

```powershell
pytest -m sanity -q
```

Run the optional performance smoke:

```powershell
pytest -m slow tests/test_performance.py -q
```

Collect targeted coverage for the AI pipeline:

```powershell
pytest --cov=app.services.fusion --cov=app.services.text_emotion --cov=app.services.acoustic_emotion --cov=app.routes.mood_routes --cov-report=term-missing
```

# Fixtures

Test fixtures live in `tests/fixtures/`.

- `real_audio/` contains short committed WAV files used for Layer 4.
- Other WAV fixtures support unit and integration coverage for upload validation, stereo handling, and size limits.

When adding a new real-audio fixture:

1. Keep it short, ideally 2-3 seconds.
2. Keep the total fixture footprint small; the current real-audio set is under 5 MB.
3. Prefer clearly licensed sources or team-recorded audio.
4. Update `tests/test_real_audio_sanity.py` with the expected label behavior and transcript keywords.
5. Re-run `pytest -m sanity -q` before committing.
