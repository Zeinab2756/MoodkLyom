# TEXT_FACADE_DIAGNOSIS

## Scope

Investigate why the text-emotion facade fell through to `keyword` on all validation clips, without changing application behavior.

Validation target used:

```powershell
python scripts/diagnose_mood.py tests/fixtures/validation/same_text_1_happy.wav --text-only
```

## Short Answer

- Yes, the BERT classifier is being attempted on the first call.
- It does **not** load successfully.
- The immediate failure is a `JSONDecodeError` while `transformers` tries to read `app/models/bert_emotion_model/tokenizer_config.json`.
- The root cause is that `app/models/bert_emotion_model/` contains **Git LFS pointer files**, not actual model/tokenizer artifacts.
- Because the local directory exists, the loader always prefers it over the remote Hugging Face model name, so it never falls back to the working remote model.
- After the first failure, the singleton classifier sets `_load_attempted=True`, so later calls in the same process do **not** retry BERT. They return an empty result, which the facade then rejects and falls through.
- The external fallback is also unavailable in this environment, so the facade ends up at `keyword`.

## CLI Result

Observed output from:

```powershell
python scripts/diagnose_mood.py tests/fixtures/validation/same_text_1_happy.wav --text-only
```

Key lines:

- Transcription succeeded via `faster-whisper (local)`
- Transcript: `Kids are talking by the door!`
- Text emotion backend reported by the CLI: `keyword fallback`
- Final text-only fused mood: `neutral`

Important limitation of the current CLI:

- `scripts/diagnose_mood.py` does **not** currently log whether BERT was attempted and failed.
- It only shows the backend that ultimately won after fallback.
- I therefore verified the BERT path directly with targeted shell probes below.

## Was BERT Attempted?

Yes.

Direct probe:

```python
from app.models.emotion_model import EmotionClassifier
classifier = EmotionClassifier()
classifier.predict_emotion("Kids are talking by the door!")
```

Observed behavior on the first call:

- `EmotionClassifier._ensure_loaded()` is entered
- `AutoTokenizer.from_pretrained(model_source)` is called
- It raises `json.decoder.JSONDecodeError`

The facade then catches that broad exception here in [app/services/text_emotion.py](/c:/Users/AUB/OneDrive%20-%20American%20University%20of%20Beirut/Desktop/moodaklyom/MoodakLyom/app/services/text_emotion.py):

```python
try:
    bert_result = emotion_classifier.predict_emotion(normalized_text)
    emotion = _to_emotion_distribution(bert_result, source="bert")
    if emotion.confidence > 0:
        return emotion
except Exception:
    pass
```

So the first BERT attempt is real, but the exception is swallowed.

## Did BERT Load Successfully?

No.

Exact exception from a direct call:

```text
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Relevant stack:

- `EmotionClassifier.predict_emotion()`
- `EmotionClassifier._ensure_loaded()`
- `transformers.AutoTokenizer.from_pretrained(model_source)`
- `transformers.models.auto.tokenization_auto.get_tokenizer_config(...)`
- `json.load(reader)` on `tokenizer_config.json`

This fails before tokenizer/model initialization completes, so:

- `self.tokenizer` stays `None`
- `self.model` stays `None`
- no BERT prediction is produced

## What Did BERT Return?

On the **first** call in a fresh process:

- It returned **nothing**
- It raised `JSONDecodeError`

On the **second** call in the same process:

- It did **not** retry loading
- `_ensure_loaded()` returned `False` because `_load_attempted=True` and `self.model is None`
- `predict_emotion()` returned:

```python
{
  "primary_emotion": None,
  "confidence": 0.0,
  "alternative_emotions": [],
  "distribution": {},
}
```

That means there are two different fallthrough modes:

1. First call: exception-driven fallthrough
2. Later calls in the same process: empty-result fallthrough

## Why Did the Facade Fall Through to Keyword Instead of Using BERT?

There are two layers of fallthrough:

### Layer 1: BERT path fails

First call:

- `emotion_classifier.predict_emotion(...)` raises `JSONDecodeError`
- `predict_text_emotion_async()` catches `Exception` and suppresses it

Later calls in the same process:

- `emotion_classifier.predict_emotion(...)` returns an empty structure
- `_to_emotion_distribution(...)` cannot derive a usable label
- it raises:

```text
ValueError: Emotion result did not include a usable label
```

That `ValueError` is also swallowed by the same broad `except Exception: pass`.

### Layer 2: External API path fails

The next fallback is `predict_external_emotion(...)` in [app/services/emotion_detection.py](/c:/Users/AUB/OneDrive%20-%20American%20University%20of%20Beirut/Desktop/moodaklyom/MoodakLyom/app/services/emotion_detection.py).

Configured default:

```text
EMOTION_API_URL = http://0.0.0.0:8000/emotion/emotion/analyze
```

Observed direct failure:

```text
ConnectionError: Emotion API at http://0.0.0.0:8000/emotion/emotion/analyze is not available
```

So the facade falls through one more time:

- BERT unavailable
- external API unavailable
- keyword fallback wins

## Exact Trigger Causing the Fallthrough

Primary trigger on the first call:

```text
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Why it happens:

- `tokenizer_config.json` is not JSON
- it is a Git LFS pointer stub

Secondary trigger on subsequent calls in the same process:

```text
ValueError: Emotion result did not include a usable label
```

Why it happens:

- `_load_attempted=True`
- `_ensure_loaded()` returns `False`
- `predict_emotion()` returns empty values
- `_to_emotion_distribution()` rejects the empty result

## Model Directory Audit

Directory inspected: [app/models/bert_emotion_model](/c:/Users/AUB/OneDrive%20-%20American%20University%20of%20Beirut/Desktop/moodaklyom/MoodakLyom/app/models/bert_emotion_model)

Files present:

- `config.json`
- `special_tokens_map.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `vocab.txt`

Files **not** present:

- `pytorch_model.bin`
- `model.safetensors`

Actual contents of the present files are not model JSON/tokenizer data. They are Git LFS pointers, e.g.:

```text
version https://git-lfs.github.com/spec/v1
oid sha256:...
size ...
```

This is true for all inspected files in that directory.

Conclusion:

- The repo does **not** currently contain usable local BERT assets.
- It contains LFS pointer stubs only.

## Transformers Compatibility Check

Pinned version in [requirements.txt](/c:/Users/AUB/OneDrive%20-%20American%20University%20of%20Beirut/Desktop/moodaklyom/MoodakLyom/requirements.txt):

- `transformers==4.46.3`

Compatibility check against the remote fallback model name:

- Model name in code: `bhadresh-savani/bert-base-uncased-emotion`
- Direct test with current environment succeeded:
  - `AutoTokenizer.from_pretrained("bhadresh-savani/bert-base-uncased-emotion")`
  - `AutoModelForSequenceClassification.from_pretrained("bhadresh-savani/bert-base-uncased-emotion")`

Observed remote labels:

```python
{0: 'sadness', 1: 'joy', 2: 'love', 3: 'anger', 4: 'fear', 5: 'surprise'}
```

Conclusion:

- `transformers==4.46.3` is compatible with the remote model configuration.
- The failure is **not** caused by a `transformers` version mismatch.
- The failure is caused by the local directory shadowing the remote model while containing invalid LFS pointer files.

## Findings

1. The BERT classifier is attempted on the first call.
2. It fails before inference due to invalid local tokenizer/model artifacts.
3. The local model directory contains Git LFS pointer stubs instead of real files.
4. Because the directory exists, the loader never uses the working remote Hugging Face model.
5. After the first failure, `_load_attempted=True` suppresses future retries in the same process.
6. The facade hides both the original `JSONDecodeError` and subsequent empty-result failure.
7. The external fallback is also unavailable by default in this environment.
8. The final observed behavior is therefore always `keyword` fallback.

## Proposed Fixes

Not applied yet. These are diagnosis-driven recommendations only.

### 1. Fix local model asset handling

Choose one of:

- Commit the actual BERT artifacts correctly via Git LFS and ensure they are pulled in CI/dev environments.
- Or remove/ignore the broken local directory and intentionally load from `bhadresh-savani/bert-base-uncased-emotion`.

### 2. Validate local model files before using them

Before selecting `self.local_model_dir` as `model_source`, validate that the directory contains real model artifacts, not LFS pointers.

At minimum:

- detect LFS pointer content in JSON/tokenizer files
- require either `pytorch_model.bin` or `model.safetensors`

If validation fails, skip the local directory and fall back to the remote model name.

### 3. Surface the real BERT failure

The facade should not silently swallow the initial BERT exception with no trace.

Recommended:

- log the exception type and message
- expose the chosen backend and failure reason in the diagnostic CLI

### 4. Reconsider `_load_attempted` behavior after failed initialization

Current behavior:

- first call raises
- later calls stop retrying and return empty results

Recommended:

- store the original initialization exception explicitly
- either re-raise it on later calls, or expose a stable failure reason
- avoid converting a real load failure into an opaque empty prediction

### 5. Tighten fallback semantics in `predict_text_emotion_async`

Current behavior:

- any exception in BERT path triggers fallback
- empty/invalid BERT results also end up in fallback

Recommended:

- distinguish between:
  - model load failures
  - inference failures
  - empty-result contract violations
- log which condition caused the fallback

### 6. Fix or remove the default external fallback URL

Current default:

```text
http://0.0.0.0:8000/emotion/emotion/analyze
```

That is not a valid default target for local loopback use on Windows.

Recommended:

- use a valid local default if intended, or
- require explicit configuration and skip the external step when unset

## Bottom Line

The validation report was correct to say the facade fell through to `keyword` on all clips.

The underlying reason is not that BERT produced neutral results. The real reason is:

- local BERT assets are broken/incomplete,
- the code prefers those broken local assets,
- the failure is swallowed,
- the external fallback is unavailable,
- so the facade ends at `keyword`.
