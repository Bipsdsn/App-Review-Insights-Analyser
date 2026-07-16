# Conventions: App Review Insights Analyser

> Companion to `architecture.md` and `dataflow.md`. These conventions keep the codebase consistent, safe, and easy to re-run week after week.

## 1. Project & File Conventions

### 1.1 Directory Layout

Follow the structure in `architecture.md` §4 exactly. Rules:

- `src/` — all pipeline code. One module per pipeline stage.
- `prompts/` — every LLM prompt lives in its own `.txt` file. **No prompts hardcoded in Python strings.**
- `data/` — inputs and intermediate datasets. Git-ignored except a small `sample_reviews.csv` for the deliverable.
- `output/` — generated artifacts. Git-ignored except the latest weekly note kept for submission.
- Root — only `run_pipeline.py`, `config.yaml`, `README.md`, `requirements.txt`, `.env.example`, `.gitignore`.

### 1.2 File Naming

| Kind | Convention | Example |
|---|---|---|
| Python modules | `snake_case.py`, verb_noun for stages | `import_reviews.py`, `generate_note.py` |
| Prompts | `snake_case.txt`, named after the task | `theme_discovery.txt` |
| Dated artifacts | `{name}_YYYY-MM-DD.{ext}` (ISO dates only) | `weekly_note_2026-07-15.md` |
| Config | lowercase, `.yaml` | `config.yaml` |
| Archives | `archive/` subfolder inside `output/` | `output/archive/theme_counts_2026-07-08.json` |

### 1.3 Git Conventions

- **`.gitignore` must include**: `.env`, `data/raw/`, `data/*.csv` (except `sample_reviews.csv`), `output/` (except the submitted note), `__pycache__/`
- Commit messages: imperative, prefixed by stage — `import: handle empty Play Store titles`, `note: add compress retry`
- Never commit: API keys, raw review dumps, anything pre-PII-boundary

## 2. Python Code Conventions

### 2.1 Style

- Python 3.10+, PEP 8, formatted with `black` (default settings), imports sorted with `isort`
- Type hints on all public function signatures
- Docstrings on every module and public function (one-line summary + args/returns for non-trivial ones)
- Max function length ~40 lines; split stage logic into small pure helpers

### 2.2 Module Pattern

Every stage module follows the same shape so `run_pipeline.py` can chain them uniformly:

```python
"""Stage 2: Group reviews into <=5 themes via LLM classification."""

def run(config: dict) -> Path:
    """Execute this stage. Reads previous stage's file, writes own output.

    Returns the path of the primary output file.
    """
```

- Each stage **reads only from disk** (previous stage's file) and **writes only its own outputs** — no cross-stage in-memory coupling. This is what makes `--from <stage>` re-runs possible.
- Stages must be idempotent: running twice with the same inputs produces the same outputs (LLM temperature pinned low, see §4.2).

### 2.3 Error Handling

- Validate at boundaries only: config load, external API responses, LLM JSON parsing
- Raise `PipelineError` (single custom exception in `src/errors.py`) with a stage-prefixed message: `PipelineError("group: LLM returned unknown theme 'Billing'")`
- Never swallow exceptions silently; log then re-raise or handle explicitly
- Atomic writes: write to `*.tmp` then rename, so a crash never leaves a half-written CSV

### 2.4 Logging

- Use the stdlib `logging` module, never bare `print` (exception: final user-facing summary in `run_pipeline.py`)
- One logger per module: `log = logging.getLogger(__name__)`
- Levels: `INFO` for stage progress ("classified 250/1000"), `WARNING` for recoverable issues (retry, redaction hit), `ERROR` before raising
- **Never log review text or anything pre-scrub** — logs are artifacts too and must be PII-free

## 3. Data Conventions

### 3.1 Canonical Review Schema

All code uses these exact column names — no aliases, no renames mid-pipeline:

| Column | Type | Rules |
|---|---|---|
| `review_id` | str | `sha256(platform_id)[:10]`, lowercase hex |
| `store` | str | exactly `play` or `appstore` |
| `rating` | int | 1–5 inclusive; rows outside range dropped with WARNING |
| `title` | str | empty string if absent (never NaN) |
| `text` | str | PII-scrubbed; empty rows dropped |
| `date` | str | ISO 8601 `YYYY-MM-DD` only |
| `theme` | str | added by Stage 2; must match legend exactly |

### 3.2 Dates & Time

- All dates ISO 8601, all internal datetimes UTC
- The "week" boundary is computed as `today - N*7 days` at pipeline start and passed down — never recomputed mid-run

### 3.3 PII Rules (Non-Negotiable)

1. Raw source data (with usernames) exists **in memory only** — never written to disk, never logged, never sent to any API
2. The regex scrub set lives in one place: `pii_scrub.py::PATTERNS`. Any new pattern goes there, nowhere else
3. Redaction placeholder is always the literal `[REDACTED]`
4. Every artifact-producing stage re-runs the PII scan on its own output (defense in depth)
5. Adding a new data source? It must route through `pii_scrub.run()` before anything else

## 4. LLM Conventions

### 4.1 Prompt Files

- One task = one file in `prompts/`. Use `{placeholder}` for variables, filled via `str.format`
- Every prompt must specify: role/tone, exact output format (JSON schema or markdown skeleton), and hard constraints restated (≤5 themes, ≤250 words, verbatim quotes only)
- Prompt changes are code changes: commit them with a message explaining the behavior change

### 4.2 API Calls (Groq)

- All calls go through `llm_client.py` — no direct `groq` SDK usage in stage modules
- Settings pinned in one place: `model=llama-3.3-70b-versatile`, `temperature=0.2` (classification: `0.0`), `response_format=json` where supported
- Rate limiting: 2s sleep between calls; exponential backoff (2s, 4s, 8s) on 429/5xx, max 3 retries
- JSON responses: parse → on failure, one "return valid JSON only" reprompt → on second failure, raise `PipelineError`
- Batch size for classification: 25 reviews per call (defined as `BATCH_SIZE` constant, not a magic number)

### 4.3 Output Validation (always in code, never trust the LLM)

| LLM output | Validator |
|---|---|
| Theme legend | ≤5 themes, non-empty names, deduped |
| Classifications | theme ∈ legend; unknown → 1 retry → `Other` |
| Weekly note | ≤250 words; quotes are substrings of source CSV; PII re-scan |

## 5. Configuration & Secrets

- **`config.yaml`** — all tunables (app IDs, window weeks, provider, email mode). No secrets ever
- **`.env`** — secrets only: `GROQ_API_KEY`. Loaded via `python-dotenv`. Ship `.env.example` with placeholder values
- Code reads config once at startup in `run_pipeline.py` and passes the dict down — stages never read files/env directly
- `window_weeks` validated at load: must be 8–12, else fail fast with a clear message

## 6. CLI Conventions

`run_pipeline.py` is the single entry point:

```
python run_pipeline.py                  # full run, defaults from config.yaml
python run_pipeline.py --weeks 10      # override window
python run_pipeline.py --from group    # resume from a stage: import|group|note|email
python run_pipeline.py --reuse-legend  # pin last week's themes for consistent trends
python run_pipeline.py --dry-run       # everything except LLM calls + email (uses cached/stub data)
```

- Flags override `config.yaml`; config overrides built-in defaults
- Exit codes: `0` success, `1` pipeline error, `2` config error

## 7. Testing Conventions

- Framework: `pytest`, tests in `tests/`, files named `test_<module>.py`
- **Must-have tests** (cheap, no network):
  - `pii_scrub`: known PII strings are redacted; clean text is untouched
  - `import`: window filter boundaries (exactly 8 and 12 weeks), schema mapping per source
  - `note validation`: word counter, quote substring checker
- LLM calls are mocked in tests — a `FakeLLM` returning canned JSON lives in `tests/conftest.py`
- Run before every commit: `pytest -q`

## 8. Documentation Conventions

- `README.md` must always contain: setup (3 steps max), **how to re-run for a new week** (one command), and the current **theme legend** (copied from `output/theme_legend.md`)
- Update the README theme legend whenever the legend changes
- Doc files in the repo root use lowercase kebab/plain names: `architecture.md`, `dataflow.md`, `conventions.md`

## 9. Weekly Note Style Guide (Tone Control)

- Voice: neutral, factual, leadership-ready. No hype, no blame
- Structure (fixed skeleton):
  1. Title line with week ending date
  2. **Top 3 Themes** — name, count, avg rating, one-line summary each
  3. **What Users Are Saying** — 3 verbatim quotes with theme tags
  4. **Recommended Actions** — 3 numbered, concrete, owner-suggestable ideas
- Numbers over adjectives: "214 reviews, avg 1.8★" not "lots of angry users"
- Quotes shown in italics with quotation marks, no attribution of any kind
- Total ≤250 words, headers + bullets only, no paragraphs longer than 2 sentences
