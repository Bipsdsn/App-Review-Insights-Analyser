# Data Flow: App Review Insights Analyser

> Companion to `architecture.md`. Traces every piece of data from source to final artifact, showing the exact shape of data at each hop, which component touches it, and where constraints are enforced.

## 1. End-to-End Flow Diagram

```
  EXTERNAL SOURCES                      PIPELINE                            ARTIFACTS
┌────────────────────┐
│ Play Store (public)│──┐
│ google-play-scraper│  │
└────────────────────┘  │   ┌──────────────────┐
┌────────────────────┐  ├──▶│ import_reviews.py │
│ App Store RSS feed │──┤   │  fetch + window   │
│ (itunes.apple.com) │  │   │  filter + merge   │
└────────────────────┘  │   └────────┬─────────┘
┌────────────────────┐  │            │ raw rows (in memory only)
│ Manual CSV exports │──┘            ▼
│ data/raw/*.csv     │      ┌──────────────────┐
└────────────────────┘      │   pii_scrub.py   │ ◀── PII BOUNDARY: nothing past
                            │ drop cols, regex │     this point contains PII
                            │ redact, hash IDs │
                            └────────┬─────────┘
                                     │ writes
                                     ▼
                            ┌──────────────────┐
                            │ data/reviews.csv │ ─────────────────▶ 📦 Deliverable 4
                            └────────┬─────────┘                    (Reviews CSV)
                                     │
                     ┌───────────────┴───────────────┐
                     ▼ (sample ~100)                 ▼ (all, batches of 25)
            ┌──────────────────┐            ┌──────────────────┐
            │ Groq LLM call #1 │            │ Groq LLM calls   │
            │ theme discovery  │───legend──▶│ #2..#N classify  │
            └────────┬─────────┘            └────────┬─────────┘
                     │ writes                        │ writes
                     ▼                               ▼
        ┌────────────────────────┐      ┌──────────────────────────┐
        │ output/theme_legend.md │      │ data/reviews_themed.csv  │
        │ (→ README)  📦 Deliv 5 │      │ output/theme_counts.json │
        └────────────────────────┘      └────────────┬─────────────┘
                                                     │ aggregates + quotes pool
                                                     ▼
                                        ┌──────────────────────────┐
                                        │ generate_note.py         │
                                        │ Groq LLM call (final)    │
                                        │ + validators (words,     │
                                        │   quotes, PII re-scan)   │
                                        └────────────┬─────────────┘
                                                     │ writes
                                                     ▼
                                   ┌────────────────────────────────┐
                                   │ output/weekly_note_YYYY-MM-DD.md│ ──▶ 📦 Deliverable 2
                                   └────────────────┬───────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────┐
                                        │ draft_email.py       │
                                        │ .eml file OR Gmail   │
                                        │ draft (to self)      │
                                        └──────────┬───────────┘
                                                   │
                                                   ▼
                                   ┌────────────────────────────┐
                                   │ output/email_draft.eml     │ ──▶ 📦 Deliverable 3
                                   │ (or Gmail Drafts folder)   │
                                   └────────────────────────────┘
```

## 2. Stage-by-Stage Data Contracts

### Stage 0 → 1: Source Data (external, transient)

Raw review objects as returned by each source. **Held in memory only — never written to disk in raw form.**

| Source | Raw fields received | PII fields present |
|---|---|---|
| `google-play-scraper` | reviewId, userName, content, score, at (datetime) | userName, reviewId |
| App Store RSS (JSON) | id, author.name, title, content, im:rating, updated | author.name, id |
| Manual CSV in `data/raw/` | varies | possibly username/email columns |

**Transformations applied by `import_reviews.py`:**
1. Map source fields → canonical schema (`store`, `rating`, `title`, `text`, `date`)
2. Parse dates to ISO 8601 (`YYYY-MM-DD`)
3. Filter: `date >= today - (window_weeks * 7 days)` — window validated to be 8–12 weeks
4. Merge both stores, dedupe on `(store, hashed_id)`, sort by date descending

### Stage 1 → 1.5: PII Boundary (`pii_scrub.py`)

**This is the single most important hop.** Everything downstream (files, LLM prompts, note, email) receives only scrubbed data.

| Operation | Input | Output |
|---|---|---|
| Column drop | userName, author, email columns | ❌ never stored |
| ID hashing | platform reviewId | `sha256(id)[:10]` → `review_id` |
| Text regex redaction | review text/title | emails, phone numbers, @handles, long numeric IDs, tokenized URLs → `[REDACTED]` |

**Output file — `data/reviews.csv`** (first artifact on disk):

```csv
review_id,store,rating,title,text,date
a3f9c01b2e,play,1,,"App keeps crashing during KYC step. Waited 3 days [REDACTED]",2026-07-10
7bd402ee91,appstore,5,"Love it","Withdrawals are instant now, great update",2026-07-09
```

### Stage 1.5 → 2: Theme Grouping (`group_themes.py`)

**Data sent to Groq — Pass 1 (theme discovery, 1 call):**
- Sample of ~100 reviews, each truncated to 200 chars: `[{rating, text}, ...]`
- Prompt asks for ≤5 themes with one-line definitions, JSON response

**Data received — theme legend:**

```json
{
  "themes": [
    {"name": "KYC / Verification", "definition": "Identity verification delays, document rejections"},
    {"name": "Payments", "definition": "Failed or stuck payment transactions"},
    {"name": "Withdrawals", "definition": "Withdrawal speed, limits, failures"},
    {"name": "Onboarding", "definition": "Signup flow, first-use confusion"},
    {"name": "App Stability", "definition": "Crashes, freezes, login errors"}
  ]
}
```

→ Written to `output/theme_legend.md`. Code asserts ≤5 themes (truncates extras).

**Data sent to Groq — Pass 2 (classification, ~40 calls for 1,000 reviews):**
- Fixed legend + batch of 25 reviews: `[{review_id, text}, ...]`
- 2-second sleep between calls (stays under ~30 req/min free tier)

**Data received per batch:**

```json
{"a3f9c01b2e": "KYC / Verification", "7bd402ee91": "Withdrawals", ...}
```

**Validation on receipt:** every returned theme must exist in the legend; unknown → retried once, then labeled `Other` (folded into nearest theme at aggregation). Malformed JSON → "fix format" reprompt (max 2).

**Output files:**
- `data/reviews_themed.csv` = `reviews.csv` + `theme` column
- `output/theme_counts.json`:

```json
{
  "week_ending": "2026-07-12",
  "totals": {"KYC / Verification": 214, "Payments": 158, "App Stability": 96, "Withdrawals": 61, "Onboarding": 44},
  "avg_rating": {"KYC / Verification": 1.8, "Payments": 2.1, "App Stability": 1.6, "Withdrawals": 3.9, "Onboarding": 2.7}
}
```

### Stage 2 → 3: Weekly Note (`generate_note.py`)

**Data assembled in code (not LLM) before the call:**
- Top 3 themes by volume, with counts + avg rating
- Week-over-week deltas (if a previous `theme_counts.json` exists)
- Quote candidate pool: 10–15 vivid, PII-scrubbed review texts from the top 3 themes (pre-filtered by code: length 40–200 chars, rating extremes preferred)

**Data sent to Groq (1 call):** stats + quote pool + strict prompt contract (top 3 themes, exactly 3 verbatim quotes from the pool, 3 action ideas, ≤250 words, neutral leadership tone).

**Data received:** Markdown note.

**Validation gates (code):**

| Gate | Check | On failure |
|---|---|---|
| Word count | ≤250 words | 1 compress retry → hard truncate |
| Quote authenticity | each quote is a substring of `reviews.csv` text | reject, re-select from pool |
| PII re-scan | regex sweep of final note | redact + log warning |

**Output:** `output/weekly_note_YYYY-MM-DD.md`

### Stage 3 → 4: Email Draft (`draft_email.py`)

**Input:** the validated note markdown + `email` config (`mode`, `to`).

| Mode | Data flow | Output |
|---|---|---|
| `eml` (default) | note → MIME message (Subject: `Weekly App Review Pulse — {date}`, To: self) | `output/email_draft.eml` |
| `gmail` | note → Gmail API `users.drafts.create` (OAuth, own account) | draft in own Gmail Drafts |

Draft only — nothing is auto-sent.

## 3. Data at Rest — Complete File Inventory

| File | Producer | Contains PII? | Retained across runs? |
|---|---|---|---|
| `data/raw/*.csv` | user (manual drops) | possibly (pre-boundary) | yes — but scrubbed before any use |
| `data/reviews.csv` | pii_scrub | **no** | overwritten each run |
| `data/reviews_themed.csv` | group_themes | **no** | overwritten each run |
| `output/theme_legend.md` | group_themes | **no** | overwritten each run |
| `output/theme_counts.json` | group_themes | **no** | archived as dated copy for WoW deltas |
| `output/weekly_note_YYYY-MM-DD.md` | generate_note | **no** | kept (dated) |
| `output/email_draft.eml` | draft_email | **no** | overwritten each run |

## 4. Data Sent to Third Parties

| Recipient | What is sent | What is never sent |
|---|---|---|
| Groq API | scrubbed review text, ratings, hashed IDs, aggregate stats | usernames, emails, raw platform IDs, phone numbers |
| Gmail API (optional) | final note text, own address | review dataset |

Both hops occur **after** the PII boundary, so no PII can leave the machine.

## 5. Weekly Re-Run Flow

```
Week N run                              Week N+1 run
──────────                              ────────────
theme_counts.json (dated archive) ────▶ read as "previous week"
                                        │
                                        ▼
                                   WoW deltas computed
                                        │
                                        ▼
                                   included in note stats
                                   ("KYC complaints ↑ 32% WoW")
```

Everything else is stateless: `python run_pipeline.py` recomputes the window from today's date, re-imports, re-classifies against a freshly discovered (or pinned) legend, and emits new dated artifacts. To pin the legend across weeks for consistent trend lines, keep `output/theme_legend.md` and pass `--reuse-legend`.

## 6. Failure Propagation

| Failure point | Data state left behind | Recovery |
|---|---|---|
| Import fails (network) | nothing written | rerun; or drop manual CSV in `data/raw/` |
| Classification fails mid-way | partial in-memory only; `reviews_themed.csv` written atomically at end | rerun stage — `run_pipeline.py --from group` |
| Note validation exhausts retries | last candidate note saved with `.FAILED.md` suffix | manual review, rerun `--from note` |
| Email draft fails | note still on disk | rerun `--from email` |

Each stage reads only from the previous stage's file, so any stage can be re-run independently without repeating upstream LLM calls.
