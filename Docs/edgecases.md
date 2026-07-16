# Edge Cases (Living Document): App Review Insights Analyser

> **Living document** — updated as new edge cases are discovered during development, testing, and weekly runs. Companion to `architecture.md`, `dataflow.md`, `conventions.md`, and `implementation-plan.md`.
>
> **How to use**: When you hit a new edge case, add a row with a stable ID, the handling decision, and status. Never delete entries — mark them `Resolved` or `Won't Fix` so the history stays searchable.
>
> **Status legend**: 🟢 Handled (code + test) · 🟡 Handled (code only) · 🔵 Planned · ⚪ Open / undecided · ⛔ Won't fix (documented risk)

**Last updated**: 2026-07-15

---

## 1. Import Stage (EC-IMP)

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| EC-IMP-01 | Play Store review has empty/missing `content` | Drop row, count in WARNING log summary | 🔵 |
| EC-IMP-02 | App Store RSS returns fewer than 10 pages / empty pages mid-loop | Stop pagination on first empty page; proceed with what was fetched | 🔵 |
| EC-IMP-03 | App Store RSS entry is app metadata (first entry of page 1 is the app itself, not a review) | Skip entries missing `im:rating` | 🔵 |
| EC-IMP-04 | Review date exactly on the window boundary (today − weeks×7) | Inclusive: `date >= cutoff` kept. Boundary tested at exactly 8 and 12 weeks | 🔵 |
| EC-IMP-05 | Zero reviews in window from BOTH sources | Fail fast with `PipelineError("import: 0 reviews in window")` — a note from nothing is worse than no note | 🔵 |
| EC-IMP-06 | Very few reviews (<20) in window | Proceed but stamp the note header with "Low volume week (N reviews)" so readers calibrate | 🔵 |
| EC-IMP-07 | Same user cross-posts identical text on both stores | Not deduped (different store = different datapoint). Dedupe key is `(store, hashed_id)` only | ⛔ |
| EC-IMP-08 | Duplicate rows from scraper pagination overlap | Deduped on `(store, hashed_id)` before write | 🔵 |
| EC-IMP-09 | Rating outside 1–5 (malformed source / manual CSV) | Drop row with WARNING | 🔵 |
| EC-IMP-10 | Manual CSV in `data/raw/` has unknown column names | Best-effort mapping via alias table (`content/body/review → text` etc.); unmappable file → skip with ERROR listing found columns | 🔵 |
| EC-IMP-11 | Manual CSV has no date column | Reject file — window filtering is impossible without dates | 🔵 |
| EC-IMP-12 | Dates in local formats (`15/07/2026`, `Jul 15, 2026`) or with timezones | Parse with pandas `to_datetime(utc=True)`, normalize to ISO date; unparseable → drop row with WARNING | 🔵 |
| EC-IMP-13 | Future-dated review (clock skew / bad source data) | Clamp: drop rows with `date > today` with WARNING | 🔵 |
| EC-IMP-14 | Play Store scraper library breaks (Google page structure change) | Documented fallback: manual public CSV into `data/raw/` (see architecture §7) | 🟡 |
| EC-IMP-15 | Network timeout / connection reset mid-fetch | Retry 3× with backoff; on final failure raise `PipelineError` — nothing partial written | 🔵 |
| EC-IMP-16 | Review text is emoji-only or single character | Keep (it carries a rating); excluded from quote pool by the 40-char minimum | 🔵 |
| EC-IMP-17 | Non-English reviews (Hindi, Hinglish, etc.) | Keep — LLM classifies multilingual text fine. Quote pool prefers English but doesn't require it; prompt says "quote verbatim, do not translate" | 🔵 |
| EC-IMP-18 | Extremely long review (>5,000 chars) | Truncate to 2,000 chars at import with `…` suffix (protects LLM context budget) | 🔵 |

## 2. PII Scrubbing (EC-PII)

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| EC-PII-01 | Email with unusual TLD or subaddressing (`a+b@x.co.in`) | Covered by RFC-ish permissive regex; tested | 🔵 |
| EC-PII-02 | Indian phone formats (`+91 98765 43210`, `098765-43210`, 10-digit bare) | Dedicated pattern set incl. optional +91/0 prefix and separators | 🔵 |
| EC-PII-03 | User signs review with their own name ("– Ramesh, Pune") | ⚠️ Names are NOT reliably regex-detectable. Mitigations: (a) quote pool prompt instructs LLM to skip quotes containing names, (b) final manual PII sweep before submission (implementation-plan §7). Residual risk documented | 🟡 |
| EC-PII-04 | Order/ticket/account numbers of varying lengths | 8+ consecutive digits → `[REDACTED]`. Shorter numbers (amounts, days) intentionally kept — they're signal, not PII | 🔵 |
| EC-PII-05 | Currency amounts with many digits (`₹1,00,000`) | Comma/₹-prefixed number patterns excluded from the ID rule — amounts are not PII | 🔵 |
| EC-PII-06 | `@handle` vs email ambiguity | Email pattern runs first; then standalone `@\w+` | 🔵 |
| EC-PII-07 | URLs containing tracking tokens or user IDs | Any URL with query string → whole URL redacted; bare domains kept | 🔵 |
| EC-PII-08 | PII split across title and text | Both fields scrubbed with the same pipeline | 🔵 |
| EC-PII-09 | Scrubbing makes a review empty (`text == "[REDACTED]"`) | Keep row for counts/ratings; exclude from quote pool (min-length rule) | 🔵 |
| EC-PII-10 | LLM echoes redaction marker into note quotes | Quote-pool prefilter excludes candidates containing `[REDACTED]` | 🔵 |
| EC-PII-11 | Aadhaar/PAN-like patterns (`XXXX XXXX XXXX`, `ABCDE1234F`) | Dedicated patterns added (fintech context makes these likely) | 🔵 |
| EC-PII-12 | Developer replies embedded in review data (may address user by name) | Developer-reply fields never imported — mapped columns only | 🔵 |

## 3. Theme Grouping (EC-THM)

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| EC-THM-01 | LLM proposes >5 themes despite prompt | Code truncates to first 5, WARNING logged | 🔵 |
| EC-THM-02 | LLM proposes 1–2 overly broad themes ("Good", "Bad") | Discovery prompt requires topic-based (not sentiment-based) themes with concrete definitions; manual eyeball at Phase-2 checkpoint; rerun discovery with stronger instruction if bad | 🟡 |
| EC-THM-03 | Duplicate/near-duplicate theme names ("Payment", "Payments") | Case-insensitive dedupe after strip; near-dupes caught at checkpoint review | 🟡 |
| EC-THM-04 | Classification returns theme not in legend | 1 retry with explicit legend restated → else `Other` | 🔵 |
| EC-THM-05 | `Other` bucket grows large (>15% of reviews) | WARNING with sample of `Other` texts — signal that the legend misses a real theme; rerun discovery | 🔵 |
| EC-THM-06 | Review legitimately spans two themes ("KYC failed AND payment stuck") | Single-label by design (prompt: "choose the dominant issue"). Multi-label rejected for simplicity — counts stay interpretable | ⛔ |
| EC-THM-07 | Classification response missing some review_ids from the batch | Missing IDs re-queued into next batch; after 2 attempts → `Other` | 🔵 |
| EC-THM-08 | Classification response contains review_ids never sent | Ignored with WARNING (hallucinated keys) | 🔵 |
| EC-THM-09 | Batch JSON malformed | "Return valid JSON only" reprompt (max 2) then `PipelineError` (conventions §4.2) | 🔵 |
| EC-THM-10 | `--reuse-legend` but old legend no longer fits new complaints | EC-THM-05 guard fires; user decides: keep trend continuity vs re-discover | 🟡 |
| EC-THM-11 | Groq 429 despite 2s sleep (shared free-tier fluctuations) | Backoff 2/4/8s, max 3; then `PipelineError` — resumable via `--from group` | 🔵 |
| EC-THM-12 | Groq model deprecated/renamed | Model name in config, not code; fallback providers (gemini/ollama) one config line away | 🟢 |
| EC-THM-13 | Tie in theme ranking for the top-3 cut | Tiebreak: lower avg rating wins (more pain = more important) | 🔵 |

## 4. Note Generation (EC-NOTE)

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| EC-NOTE-01 | Note >250 words after compress retry | Hard truncate at section boundary (never mid-quote), append nothing | 🔵 |
| EC-NOTE-02 | LLM paraphrases a quote (fails substring check) | Re-select from pool (up to 3 attempts); final fallback: code inserts top-rated pool quotes verbatim itself | 🔵 |
| EC-NOTE-03 | Quote contains newline/smart-quotes breaking substring match | Normalize whitespace + unicode quotes on BOTH sides before comparing | 🔵 |
| EC-NOTE-04 | Fewer than 3 themes exist (small/new app) | Note renders "Top N themes" with N available; never pads with fake themes | 🔵 |
| EC-NOTE-05 | Fewer than 3 viable quotes in pool | Relax length filter to 20–300 chars; if still short, note says "Representative quotes limited this week (N)" | 🔵 |
| EC-NOTE-06 | All reviews are 5★ praise (no problems to action) | Valid outcome: actions become "amplify" ideas (prompt covers both directions) | 🔵 |
| EC-NOTE-07 | LLM invents statistics not in the provided stats block | All numbers injected by code into a stats block the prompt must copy; checkpoint eyeball for drift | 🟡 |
| EC-NOTE-08 | WoW deltas when previous week had zero for a theme | Show "new" instead of ∞% | 🔵 |
| EC-NOTE-09 | First-ever run (no previous `theme_counts`) | Skip WoW section entirely | 🔵 |
| EC-NOTE-10 | LLM adds preamble ("Here is your note:") | Strip everything before the first `#` heading | 🔵 |
| EC-NOTE-11 | Word-counting ambiguity (markdown syntax, numbers, ★) | Count on rendered-ish text: strip `#*_|` markdown tokens first; counter unit-tested | 🔵 |
| EC-NOTE-12 | Two runs on the same day overwrite the dated note | Same-day rerun overwrites (idempotent by design); pass `--tag` suffix if both needed | 🟡 |

## 5. Email Draft (EC-MAIL)

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| EC-MAIL-01 | Non-ASCII chars (₹, ★, emoji) in `.eml` body | UTF-8 with proper MIME headers (`charset=utf-8`, quoted-printable) | 🔵 |
| EC-MAIL-02 | Mail client renders markdown as plain text | Multipart: plain-text part + simple HTML part (headers → `<h3>`, bullets → `<li>`) | 🔵 |
| EC-MAIL-03 | `.eml` opens in "received" mode not draft in some clients | Acceptable — deliverable is a screenshot of the draft content; documented in README | ⛔ |
| EC-MAIL-04 | Gmail OAuth flow fails (stretch mode) | Fall back to `eml` mode automatically with WARNING | 🔵 |
| EC-MAIL-05 | `email.to` missing/invalid in config | Config validation at startup: must match basic email pattern, else exit code 2 | 🔵 |

## 6. Pipeline / Ops (EC-OPS)

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| EC-OPS-01 | `GROQ_API_KEY` missing | Fail at startup (exit 2) with setup hint — not mid-pipeline after import work | 🔵 |
| EC-OPS-02 | `--from group` but `reviews.csv` missing | Prerequisite check per stage: clear error naming the missing file and the stage to run | 🔵 |
| EC-OPS-03 | Crash mid-write corrupts CSV | Atomic writes (`*.tmp` + rename) everywhere (conventions §2.3) | 🔵 |
| EC-OPS-04 | `window_weeks` outside 8–12 (config or flag) | Validation at load, exit 2 (challenge constraint) | 🔵 |
| EC-OPS-05 | Windows path/encoding issues (dev machine is Windows) | `pathlib.Path` everywhere; all file IO `encoding="utf-8"`; no shell-dependent code | 🔵 |
| EC-OPS-06 | Clock/timezone: "week ending" ambiguity | All internal UTC; note header uses local date at run time, documented in README | 🔵 |
| EC-OPS-07 | `output/archive/` grows unboundedly | Acceptable for this project's scale (~2 small JSONs/week) | ⛔ |
| EC-OPS-08 | Two pipeline instances run simultaneously | Not guarded (single-user tool). Documented: don't do it | ⛔ |
| EC-OPS-09 | Groq free-tier daily quota exhausted (heavy re-run day) | ~43 calls/run leaves huge headroom; if hit: wait or switch `provider: ollama` in config | 🟡 |

---

## 7. Discovered During Development (append below)

> Add new entries here as they surface. Template:
>
> `| EC-XXX-NN | what happened | decision | status |`

| ID | Edge case | Handling decision | Status |
|---|---|---|---|
| _(none yet)_ | | | |

---

## 8. Known Accepted Risks (summary of ⛔ entries)

1. **Self-identifying users** (EC-PII-03): a user writing their own name in prose can slip past regex. Mitigated by LLM quote-selection instruction + manual final sweep. This is the standard practical limit of regex-based PII removal.
2. **Cross-store duplicate opinions** (EC-IMP-07): same person counted twice across stores — acceptable; store-level counts remain honest.
3. **Single-label themes** (EC-THM-06): multi-issue reviews counted once — keeps the note's numbers simple and defensible.
4. **`.eml` client quirks** (EC-MAIL-03): draft rendering varies by client — the deliverable is evidence of the draft, which any client provides.
5. **No concurrency guard / unbounded archive** (EC-OPS-07/08): out of scope for a single-user weekly tool.
