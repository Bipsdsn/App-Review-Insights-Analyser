# Architecture: App Review Insights Analyser

> **Design principle: 100% free.** Every component below runs on free tiers or open-source tools. No paid APIs, no paid hosting, no credit card required.

## 1. High-Level Overview

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐   ┌─────────────┐
│   IMPORT    │──▶│   CLEAN &    │──▶│    THEME      │──▶│   WEEKLY     │──▶│    EMAIL    │
│ reviews.csv │   │  NORMALIZE   │   │   GROUPING    │   │    NOTE      │   │    DRAFT    │
│ (both stores)│  │ (PII strip)  │   │  (LLM, ≤5)    │   │ (LLM, ≤250w) │   │ (Gmail/EML) │
└─────────────┘   └──────────────┘   └───────────────┘   └──────────────┘   └─────────────┘
      CSV              pandas           free LLM API         free LLM API      free draft
```

One command runs the whole pipeline:

```
python run_pipeline.py --weeks 10
```

## 2. Tech Stack (All Free)

| Layer | Choice | Why It's Free |
|---|---|---|
| Language | Python 3.10+ | Open source |
| Data handling | pandas | Open source |
| LLM | **Groq API (free tier)** — `llama-3.3-70b-versatile` | ~30 req/min, generous daily quota free; no card needed; extremely fast inference |
| LLM (fallback) | Google Gemini free tier or local Ollama | Both free |
| Review import | Public CSV exports + `google-play-scraper` / `app-store-web-scraper` (public pages only) | Open-source libs reading public data — complies with "no scraping behind logins" |
| Email draft | Gmail API "create draft" (free) **or** generate a `.eml` file | Gmail API is free; `.eml` needs nothing |
| Output note | Markdown → optional PDF via browser print | Free |
| Hosting/demo | Runs locally; optional free Streamlit Community Cloud for prototype link | Free tier |

## 3. Component Design

### 3.1 Import Layer (`import_reviews.py`)

**Responsibility**: Produce a single normalized `reviews.csv`.

**Inputs** (any combination):
- Play Store: public reviews via `google-play-scraper` (Python lib, hits public web pages — no login)
- App Store: public RSS feed `https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/json` (free, no auth)
- Manual CSV exports dropped into `data/raw/`

**Output schema** (`data/reviews.csv`):

| Column | Type | Notes |
|---|---|---|
| review_id | string | Hashed — never the platform's raw user ID |
| store | enum | `play` / `appstore` |
| rating | int 1–5 | |
| title | string | May be empty (Play Store) |
| text | string | |
| date | ISO date | |

**Logic**:
1. Fetch/load reviews from each source
2. Filter to the configured window (8–12 weeks, `--weeks` flag)
3. Merge, dedupe, sort by date

### 3.2 PII Scrubber (`pii_scrub.py`)

**Responsibility**: Guarantee zero PII in every downstream artifact. Runs at ingestion, before anything is written to disk.

- **Drop columns**: username, author, email — never stored
- **Regex scrub inside review text**: emails, phone numbers, URLs with tokens, long numeric IDs (account numbers), `@handles`
- Replace matches with `[REDACTED]`
- Hash any platform review ID with SHA-256 (first 10 chars) for traceability without identity

This is a deterministic, non-LLM step so the guarantee doesn't depend on model behavior.

### 3.3 Theme Grouping (`group_themes.py`)

**Responsibility**: Assign every review to exactly one of ≤5 themes.

**Two-pass LLM approach**:

1. **Pass 1 — Theme discovery** (1 LLM call): Send a sample of ~100 reviews (text truncated to 200 chars each) and ask the LLM to propose at most 5 themes with one-line definitions → this becomes the **theme legend** (saved to `output/theme_legend.md`, reused in README).
2. **Pass 2 — Classification** (batched LLM calls): Classify reviews in batches of ~25 per call against the fixed legend. Output JSON: `{review_id: theme}`. Batching keeps us well inside Groq's free-tier rate limits (~40 calls for 1,000 reviews).

**Rate-limit handling**: simple retry with exponential backoff; 2-second sleep between calls keeps under Groq's ~30 req/min limit. Groq's fast inference means the full classification pass finishes in under 2 minutes.

**Output**: `data/reviews_themed.csv` (reviews + `theme` column) and `output/theme_counts.json`.

### 3.4 Weekly Note Generator (`generate_note.py`)

**Responsibility**: Produce the ≤250-word one-page pulse note.

**Inputs**: themed reviews, theme counts, average ratings per theme, week-over-week deltas if a previous run exists.

**Single LLM call** with a strict prompt contract:
- Top 3 themes ranked by volume (with counts + avg rating)
- 3 verbatim quotes (selected from PII-scrubbed text; prompt instructs "quote exactly, do not invent")
- 3 concrete action ideas tied to the themes
- Tone: neutral, leadership-ready
- Hard limit: 250 words

**Post-generation validation** (code, not LLM):
- Word count check → if >250, one retry with "compress" instruction
- Quote verification → each quote must appear as a substring in the source CSV (prevents hallucinated quotes)
- PII regex re-scan of the final note (defense in depth)

**Output**: `output/weekly_note_YYYY-MM-DD.md`

### 3.5 Email Drafter (`draft_email.py`)

**Responsibility**: Create a draft email containing the note.

**Option A (default, zero setup)**: Generate `output/email_draft.eml` — a standards-compliant email file with subject `Weekly App Review Pulse — {date}` and the note as the body. Double-clicking opens it as a draft in any mail client. Screenshot it for the deliverable.

**Option B (nicer demo)**: Gmail API `users.drafts.create` using a free Google Cloud project + OAuth consent (personal account, free). The draft appears in your own Gmail Drafts folder addressed to yourself.

No email is auto-sent — draft only, per the brief.

### 3.6 Orchestrator (`run_pipeline.py`)

Chains stages 3.1 → 3.5 with a config file:

```yaml
# config.yaml
app:
  play_store_id: "com.example.app"
  app_store_id: "123456789"
  country: "in"
window_weeks: 10
max_themes: 5
llm:
  provider: "groq"          # groq | gemini | ollama
  model: "llama-3.3-70b-versatile"
email:
  mode: "eml"               # eml | gmail
  to: "you@example.com"
```

**Re-run for a new week** = `python run_pipeline.py`. The date window is computed from today, so each run automatically picks up fresh reviews. Previous outputs are kept in dated files for week-over-week comparison.

## 4. Project Structure

```
app-review-insights/
├── config.yaml
├── run_pipeline.py          # orchestrator (one command)
├── src/
│   ├── import_reviews.py    # Stage 1: import + window filter
│   ├── pii_scrub.py         # Stage 1.5: deterministic PII removal
│   ├── group_themes.py      # Stage 2: LLM theme discovery + classification
│   ├── generate_note.py     # Stage 3: LLM note + validation
│   ├── draft_email.py       # Stage 4: .eml / Gmail draft
│   └── llm_client.py        # provider-agnostic LLM wrapper (gemini/groq/ollama)
├── prompts/
│   ├── theme_discovery.txt
│   ├── classify_batch.txt
│   └── weekly_note.txt
├── data/
│   ├── raw/                 # optional manual CSV exports
│   ├── reviews.csv          # normalized, PII-free
│   └── reviews_themed.csv
├── output/
│   ├── theme_legend.md
│   ├── weekly_note_YYYY-MM-DD.md
│   └── email_draft.eml
└── README.md                # re-run instructions + theme legend
```

## 5. Data Flow & Constraint Enforcement

| Constraint | Where Enforced | How |
|---|---|---|
| Public exports only | Import layer | Play scraper + App Store RSS read public pages only; no auth anywhere in code |
| Max 5 themes | Theme discovery prompt + code assert | Prompt caps at 5; code truncates if LLM returns more |
| ≤250 words | Note validator | Programmatic word count + compress retry |
| Zero PII | PII scrubber + note re-scan | Deterministic regex at ingestion AND on final note |
| 8–12 week window | Import layer | `--weeks` param, validated to be 8–12 |

## 6. LLM Call Budget (Free Tier Fit)

For ~1,000 reviews over 10 weeks:

| Stage | Calls | Notes |
|---|---|---|
| Theme discovery | 1 | Sample-based |
| Classification | ~40 | Batches of 25 |
| Note generation | 1–2 | +1 possible compress retry |
| **Total** | **~43** | Well within Groq's free daily quota (1,000+ req/day for 70B models) |

Even a full re-run several times a day stays comfortably free.

## 7. Failure Modes & Mitigations

| Risk | Mitigation |
|---|---|
| LLM rate limit hit | Backoff + 2s inter-call sleep |
| LLM returns malformed JSON | JSON parse retry with "fix format" reprompt (max 2) |
| Hallucinated quotes | Substring verification against source CSV; reject and re-select |
| Note over 250 words | Automatic compress retry, then hard truncate as last resort |
| App Store RSS returns few reviews | Fall back to manual public CSV export in `data/raw/` |
| No API key available | `ollama` provider runs a local model fully offline |

## 8. Demo & Deliverables Mapping

| Deliverable | Produced By |
|---|---|
| Prototype link / demo video | Local run screen-recording (free) or Streamlit Community Cloud app |
| Weekly one-page note | `output/weekly_note_YYYY-MM-DD.md` |
| Email draft evidence | Screenshot of `.eml` opened in mail client or Gmail draft |
| Reviews CSV | `data/reviews.csv` (already PII-free by design) |
| README (re-run + theme legend) | `README.md` + auto-generated `output/theme_legend.md` |
