# App Review Insights Analyser

Turns recent PhonePe App Store + Play Store reviews into a one-page weekly
pulse note (top themes, real user quotes, action ideas) and drafts an email
containing it. Built entirely on free tiers — no paid APIs or hosting.

```
Import → PII scrub → Theme grouping (LLM) → Weekly note (LLM) → Email draft
```

## Setup (3 steps)

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and paste your free Groq API key
   (get one at console.groq.com)
3. `python run_pipeline.py`

## How to Re-Run for a New Week

One command:

```
python run_pipeline.py --reuse-legend
```

The date window is computed from today, so each run automatically picks up
fresh reviews. `--reuse-legend` pins last week's themes for consistent
week-over-week trends (omit it to re-discover themes from scratch).

Other useful flags:

| Flag | Effect |
|---|---|
| `--weeks N` | window size, 8–12 (default from config.yaml) |
| `--from {import\|group\|note\|email}` | resume from a stage without repeating earlier ones |
| `--dry-run` | walk all stages with no LLM calls or email |

Outputs land in `output/`: `weekly_note_YYYY-MM-DD.md`, `email_draft.eml`,
`theme_legend.md`, `theme_counts.json` (+ dated archive for WoW deltas).

## Theme Legend (current week)

- **General Praise & Sentiment** — Users expressing general positive or negative sentiment without specific topics.
- **Payment Failures** — Users experiencing issues with payment transactions, such as failures or delays.
- **App Performance & Compatibility** — Users reporting issues with app performance, compatibility, or usability.
- **Data Security & Privacy** — Users expressing concerns about data security, privacy, or deletion.
- **Features & Usability** — Users suggesting new features or improvements to existing features and usability.

(Regenerated each run in `output/theme_legend.md` unless `--reuse-legend` is set.)

## Privacy

- Public data sources only: Play Store public pages + iTunes public RSS feed. No logins, no scraping behind authentication.
- Zero PII by construction: usernames/authors are never written to disk; review IDs are hashed (SHA-256); emails, phone numbers, PAN/Aadhaar-like patterns, handles, and long IDs are regex-redacted at ingestion, and the final note is re-scanned.

## Tests

```
python -m pytest -q
```

45 offline tests cover the PII scrubber (adversarial probes), import window
boundaries and schema, and the note validation gates (word count, verbatim
quote verification).

## Notes on Free-Tier Limits

Groq free tier caps tokens per day per model. The pipeline splits work:
high-volume classification runs on `llama-3.1-8b-instant`, quality-critical
calls (theme discovery, note writing) on `llama-3.3-70b-versatile`, with an
automatic fallback to the fast model if the daily quota is hit.
