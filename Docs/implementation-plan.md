# Implementation Plan: App Review Insights Analyser

> Companion to `architecture.md`, `dataflow.md`, and `conventions.md`. Ordered build plan sized for the **Jul 17, 11:59 PM IST deadline** (~2 days). Each phase ends with a verifiable checkpoint so the project is always in a demoable state.

## Timeline at a Glance

| Phase | What | Est. effort | Target |
|---|---|---|---|
| 0 | Project scaffold + config | 30 min | Day 1 morning |
| 1 | Import + PII scrub (`reviews.csv`) | 2–3 hrs | Day 1 midday |
| 2 | LLM client + theme grouping | 2–3 hrs | Day 1 evening |
| 3 | Weekly note generation + validation | 2 hrs | Day 2 morning |
| 4 | Email draft | 1 hr | Day 2 midday |
| 5 | Orchestrator + re-run flags | 1 hr | Day 2 midday |
| 6 | Tests + polish | 1–2 hrs | Day 2 afternoon |
| 7 | Deliverables packaging (README, note, demo) | 1–2 hrs | Day 2 evening |

Buffer: ~3 hrs before the deadline. If time runs short, see §9 De-scope Ladder.

---

## Phase 0 — Scaffold (30 min)

**Goal**: Runnable empty skeleton.

Tasks:
1. Create the directory tree from `architecture.md` §4 (`src/`, `prompts/`, `data/raw/`, `output/`, `tests/`)
2. `requirements.txt`: `pandas`, `groq`, `google-play-scraper`, `requests`, `python-dotenv`, `pyyaml`, `pytest`
3. `config.yaml` with the real app IDs (the product from LIP challenge 4), `window_weeks: 10`, `provider: groq`, `email mode: eml`
4. `.env.example` (`GROQ_API_KEY=your_key_here`), `.gitignore` per `conventions.md` §1.3
5. `src/errors.py` with `PipelineError`; empty stage modules each exposing `run(config) -> Path`
6. `run_pipeline.py` stub that loads config + `.env`, validates `window_weeks` ∈ 8–12, calls each stage in order

**Checkpoint ✅**: `python run_pipeline.py --dry-run` executes end-to-end printing stage names, exit code 0.

---

## Phase 1 — Import + PII Scrub (2–3 hrs)

**Goal**: Real, PII-free `data/reviews.csv`.

Tasks:
1. `src/pii_scrub.py` **first** (it gates everything):
   - `PATTERNS` dict: email, phone (incl. Indian formats), `@handle`, 8+ digit IDs, tokenized URLs
   - `scrub_text(s) -> str`, `scrub_frame(df) -> df` (drops username/author/email columns, hashes IDs to `review_id`)
2. `src/import_reviews.py`:
   - Play Store fetcher via `google-play-scraper` `reviews()` (public, paginated, newest first, stop at window edge)
   - App Store fetcher via iTunes RSS JSON (loop pages 1–10, stop at window edge)
   - Manual CSV loader for `data/raw/*.csv` (best-effort column mapping)
   - Normalize → canonical schema (`conventions.md` §3.1) → route through `pii_scrub` → window filter → merge/dedupe/sort → atomic write
3. Wire into orchestrator as stage `import`

**Checkpoint ✅**: `python run_pipeline.py --from import` produces `data/reviews.csv` with real reviews; spot-check confirms no usernames/emails/IDs anywhere. This CSV is already Deliverable 4.

**Risk to test early**: both fetchers against the real app IDs — if either returns too few reviews, fall back to manual export now, not on deadline day.

---

## Phase 2 — LLM Client + Theme Grouping (2–3 hrs)

**Goal**: `data/reviews_themed.csv` + `output/theme_legend.md` + `output/theme_counts.json`.

Tasks:
1. `src/llm_client.py`:
   - `complete(prompt: str, json_mode: bool = True, temperature: float = 0.2) -> str`
   - Groq SDK, model `llama-3.3-70b-versatile`, 2s inter-call sleep, backoff 2/4/8s on 429/5xx (max 3), JSON-fix reprompt (max 2)
2. `prompts/theme_discovery.txt` — sample of ~100 truncated reviews → JSON legend, ≤5 themes with definitions
3. `prompts/classify_batch.txt` — legend + 25 reviews → `{review_id: theme}` JSON
4. `src/group_themes.py`:
   - Pass 1: discover legend (or load pinned legend with `--reuse-legend`), assert ≤5, write `theme_legend.md`
   - Pass 2: batch classify all reviews (temperature 0.0); validate theme ∈ legend, unknown → 1 retry → `Other`
   - Aggregate: counts + avg rating per theme → `theme_counts.json`; archive dated copy to `output/archive/`
5. Wire in as stage `group`

**Checkpoint ✅**: Full grouping run on real data completes in minutes; every review has a valid theme; legend reads sensibly for the product.

---

## Phase 3 — Weekly Note (2 hrs)

**Goal**: `output/weekly_note_YYYY-MM-DD.md`, ≤250 words, verified quotes.

Tasks:
1. Quote pool builder (code, in `src/generate_note.py`): from top-3 themes pick 10–15 candidates — length 40–200 chars, rating extremes preferred, already scrubbed
2. Week-over-week deltas: load newest archived `theme_counts` if present, compute % change per theme
3. `prompts/weekly_note.txt` — fixed skeleton from `conventions.md` §9: title w/ week-ending date, Top 3 Themes (count + avg★ + one-liner), 3 verbatim quotes from the pool only, 3 numbered actions, ≤250 words, neutral tone
4. Validation gates (code): word count → 1 compress retry → hard truncate; quote substring check vs `reviews.csv` → re-select on failure; PII regex re-scan
5. Wire in as stage `note`; failures save candidate as `*.FAILED.md`

**Checkpoint ✅**: Generated note passes all three gates and genuinely reads well — this exact file is Deliverable 2.

---

## Phase 4 — Email Draft (1 hr)

**Goal**: `output/email_draft.eml` (Option A default).

Tasks:
1. `src/draft_email.py`: build MIME message — Subject `Weekly App Review Pulse — {date}`, To: own address from config, body = note (plain text + simple HTML part); write `.eml` atomically
2. Verify the `.eml` opens as a draft in a local mail client / Outlook; screenshot for Deliverable 3
3. (Stretch, only if time allows) `gmail` mode via Gmail API drafts.create with OAuth

**Checkpoint ✅**: Double-clicking `email_draft.eml` shows a correctly formatted draft addressed to yourself.

---

## Phase 5 — Orchestrator Completion (1 hr)

**Goal**: One-command weekly re-run.

Tasks:
1. Finish `run_pipeline.py` CLI per `conventions.md` §6: `--weeks`, `--from {import|group|note|email}`, `--reuse-legend`, `--dry-run`
2. Stage chaining with clear INFO logs and a final user-facing summary (reviews imported, themes, note path, draft path)
3. Exit codes: 0 / 1 (pipeline) / 2 (config)

**Checkpoint ✅**: `python run_pipeline.py` runs import → group → note → email end-to-end from scratch; `--from note` reruns only the note without new classification calls.

---

## Phase 6 — Tests + Polish (1–2 hrs)

**Goal**: Confidence in the constraint-critical code paths.

Tasks (per `conventions.md` §7, all offline with `FakeLLM`):
1. `test_pii_scrub.py` — emails/phones/handles/IDs redacted; clean text untouched
2. `test_import.py` — window boundaries at exactly 8 and 12 weeks; per-source schema mapping; dedupe
3. `test_note_validation.py` — word counter, quote substring checker, truncation fallback
4. `pytest -q` green; `black` + `isort` pass over `src/`

**Checkpoint ✅**: All tests pass; a fresh clone + `pip install -r requirements.txt` + `.env` + one command reproduces the pipeline.

---

## Phase 7 — Deliverables Packaging (1–2 hrs)

**Goal**: Everything on the submission checklist.

| # | Deliverable | Action |
|---|---|---|
| 1 | Prototype / ≤3-min demo video | Screen-record one full pipeline run + opening the note and email draft |
| 2 | Weekly one-page note | Latest `output/weekly_note_*.md` (optionally print to PDF) |
| 3 | Email draft evidence | Screenshot of the `.eml` open in a mail client |
| 4 | Reviews CSV | Copy `data/reviews.csv` → `sample_reviews.csv` (trim to a representative sample if large) |
| 5 | README | Setup (3 steps), **re-run for a new week** (one command + `--reuse-legend` note), theme legend pasted from `output/theme_legend.md` |

Final sweep: grep all artifacts for `@`, digit-runs, and common name patterns as a last PII check.

**Checkpoint ✅**: Submission folder contains all five items; deadline buffer intact.

---

## 8. Build Order Rationale

- **PII scrub before import**: nothing can be written to disk until the boundary exists
- **Import before LLM work**: real data shapes the theme legend; fetcher problems are the biggest schedule risk, so surface them Day 1
- **Note before email**: email is a thin wrapper over the note
- **Tests near the end but not last**: the three tested areas (PII, window, validation) are exactly the challenge's hard constraints

## 9. De-scope Ladder (if time runs short)

Cut from the bottom, keep the top:

1. **Keep always**: import → scrub → group → note → `.eml` draft (the core brief)
2. Cut Gmail API mode → `.eml` only (already the default)
3. Cut `--reuse-legend` + WoW deltas → single-week note
4. Cut Streamlit prototype link → demo video only
5. Cut manual CSV loader → scraper/RSS sources only
6. Reduce tests to `test_pii_scrub.py` only (the non-negotiable constraint)

## 10. Definition of Done

- [ ] `python run_pipeline.py` completes end-to-end on real data, exit 0
- [ ] `data/reviews.csv` has ≥ 8 weeks of reviews, zero PII
- [ ] ≤5 themes; every review classified
- [ ] Note ≤250 words; 3 verbatim (verified) quotes; 3 actions; top 3 themes
- [ ] `.eml` draft opens correctly, addressed to self
- [ ] `pytest -q` green
- [ ] README has re-run instructions + theme legend
- [ ] All 5 deliverables packaged, PII sweep clean
