# Decisions (Living Document): App Review Insights Analyser

> **Living document** — an Architecture Decision Record (ADR) log. Every significant technical choice is recorded here with its context, the options considered, why we chose what we chose, and the consequences we accepted.
>
> **How to use**: When a new decision is made (or an old one is revisited), append a new entry with the next ID. Never edit a decided entry's substance — if a decision changes, mark it `Superseded by D-NNN` and write a new entry. This keeps the reasoning trail intact.
>
> **Status legend**: ✅ Accepted · 🔄 Superseded · ⏸️ Deferred · ❌ Rejected

**Last updated**: 2026-07-15

---

## Index

| ID | Decision | Status |
|---|---|---|
| D-001 | Zero-cost constraint governs all choices | ✅ |
| D-002 | Python + pandas as the implementation stack | ✅ |
| D-003 | Groq (llama-3.3-70b-versatile) as primary LLM | ✅ |
| D-004 | Deterministic regex PII scrubbing, not LLM-based | ✅ |
| D-005 | Public scraper + RSS for import, manual CSV as fallback | ✅ |
| D-006 | Two-pass theme grouping (discover, then classify) | ✅ |
| D-007 | Single-label theme classification | ✅ |
| D-008 | Batch size 25 for classification calls | ✅ |
| D-009 | Code-side validation of all LLM outputs | ✅ |
| D-010 | `.eml` file as default email draft mechanism | ✅ |
| D-011 | File-based stage handoff (disk, not memory) | ✅ |
| D-012 | Prompts as files, not inline strings | ✅ |
| D-013 | Hash platform review IDs instead of dropping them | ✅ |
| D-014 | Fail fast on zero reviews rather than emit empty note | ✅ |
| D-015 | Gemini → Groq switch for primary LLM | ✅ (supersedes part of early draft) |
| D-016 | No database — CSV/JSON files only | ✅ |
| D-017 | Streamlit prototype link | ⏸️ |
| D-018 | Multi-label themes | ❌ |

---

## D-001: Zero-cost constraint governs all choices

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: The builder will do this challenge entirely for free — no paid APIs, hosting, or tooling of any kind.
- **Decision**: Every component must run on a free tier or open-source software, with no credit card required anywhere. This is a hard filter applied before any other evaluation criterion.
- **Consequences**: Rules out OpenAI/Anthropic paid APIs, paid email services, and paid hosting. Free tiers bring rate limits, which shaped D-008 (batching) and the call-budget analysis in `architecture.md` §6.

## D-002: Python + pandas as the implementation stack

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Need CSV wrangling, HTTP calls, LLM SDKs, and email MIME building in a 2-day window.
- **Options**: (a) Python, (b) Node.js, (c) no-code tools (Zapier/Make free tiers).
- **Decision**: Python 3.10+ with pandas.
- **Why**: Best library coverage for every stage (`google-play-scraper`, `groq`, pandas, stdlib `email.mime`); no-code tools hit free-tier operation caps quickly and make the PII-scrub guarantee hard to prove.
- **Consequences**: Requires README setup steps (venv + pip); acceptable for the deliverable.

## D-003: Groq (llama-3.3-70b-versatile) as primary LLM

- **Date**: 2026-07-15 · **Status**: ✅ Accepted (see D-015 for history)
- **Context**: Pipeline needs ~43 LLM calls per run for theme discovery, classification, and note generation — all free.
- **Options**: (a) Groq free tier, (b) Google Gemini free tier, (c) local Ollama.
- **Decision**: Groq with `llama-3.3-70b-versatile`; Gemini and Ollama retained as one-line config fallbacks.
- **Why**: User's explicit choice; extremely fast inference (classification pass finishes in ~2 min); generous free quota (~30 req/min, 1,000+ req/day for 70B) comfortably fits the ~43-call budget; strong JSON-mode support; no card needed.
- **Consequences**: 2s inter-call sleep + backoff needed for the per-minute cap (EC-THM-11); model availability is Groq's discretion — mitigated by config-level model name and provider abstraction in `llm_client.py` (EC-THM-12).

## D-004: Deterministic regex PII scrubbing, not LLM-based

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: "No PII in any artifact" is a hard challenge constraint. PII removal could be done by regex, by an LLM pass, or both.
- **Options**: (a) regex only, (b) LLM redaction pass, (c) regex + LLM.
- **Decision**: Deterministic regex scrubbing at the ingestion boundary (a), plus regex re-scans on final artifacts. The LLM is only asked to avoid name-bearing quotes as a soft second layer (EC-PII-03).
- **Why**: A compliance guarantee must not depend on probabilistic model behavior. Regex is testable, reproducible, and runs before data ever touches disk or leaves the machine. An LLM redaction pass would also send un-scrubbed PII to a third party — self-defeating.
- **Consequences**: Free-text names in prose can slip through (accepted risk, `edgecases.md` §8.1); mitigated by quote-pool filtering and a manual final sweep.

## D-005: Public scraper + RSS for import, manual CSV as fallback

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Challenge allows public review exports only — no scraping behind logins. Play Console / App Store Connect exports require owner logins we don't have.
- **Options**: (a) `google-play-scraper` lib + iTunes public RSS, (b) manual copy-paste into CSV, (c) paid review-aggregation APIs.
- **Decision**: (a) as primary, (b) retained as fallback via `data/raw/`, (c) excluded by D-001.
- **Why**: Both sources read public, unauthenticated pages — compliant with the constraint; fully automated, satisfying the "re-run for a new week" requirement.
- **Consequences**: Scraper fragility if Google changes page structure (EC-IMP-14); RSS caps at ~500 recent reviews per country — acceptable for an 8–12 week window on one app.

## D-006: Two-pass theme grouping (discover, then classify)

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Reviews must be grouped into ≤5 themes that fit the actual product, not a hardcoded list.
- **Options**: (a) hardcode 5 themes up front, (b) embeddings + clustering (k-means), (c) LLM discovers legend then classifies against it.
- **Decision**: (c) — one discovery call on a ~100-review sample produces the legend; batched calls classify everything against that fixed legend.
- **Why**: (a) can't adapt to what users actually complain about; (b) produces unlabeled clusters needing an LLM naming step anyway and adds an embeddings dependency; (c) yields human-readable definitions that become the README theme legend deliverable directly.
- **Consequences**: Legend can drift between weeks — addressed with `--reuse-legend` (D-006a in spirit; see `dataflow.md` §5); discovery sample may miss rare themes — the `Other` >15% guard (EC-THM-05) detects this.

## D-007: Single-label theme classification

- **Date**: 2026-07-15 · **Status**: ✅ Accepted (rejects D-018)
- **Context**: Some reviews mention multiple issues ("KYC failed AND payment stuck").
- **Options**: (a) single label per review, (b) multi-label.
- **Decision**: Single label — prompt instructs "choose the dominant issue."
- **Why**: Counts stay interpretable (sum of theme counts = total reviews), the weekly note's numbers are defensible to leadership, and the classification output stays a simple `{id: theme}` map. Multi-label would inflate counts and complicate ranking for marginal insight gain.
- **Consequences**: Secondary issues in a review are undercounted (accepted, EC-THM-06).

## D-008: Batch size 25 for classification calls

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: ~1,000 reviews must be classified within Groq's free-tier per-minute cap and JSON reliability limits.
- **Options**: 1/call (accurate, 1,000 calls), 100/call (10 calls, high malformed-JSON risk), 25/call.
- **Decision**: 25 reviews per call (~40 calls), defined as a `BATCH_SIZE` constant.
- **Why**: Sweet spot measured against three constraints: rate limit (40 calls × 2s sleep ≈ 2.5 min), JSON response reliability (25-key objects parse dependably), and prompt context size with the legend included.
- **Consequences**: Missing/hallucinated IDs per batch need handling (EC-THM-07/08); trivially tunable if reliability data suggests otherwise.

## D-009: Code-side validation of all LLM outputs

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: The challenge has hard, checkable constraints (≤5 themes, ≤250 words, real quotes, zero PII). LLMs follow instructions most — not all — of the time.
- **Decision**: Every LLM output passes deterministic validators: legend truncation, theme-membership checks, word count with compress retry, quote substring verification against the source CSV, and a PII re-scan of the final note.
- **Why**: "The prompt says so" is not evidence. Verifiable constraints should be verified; this also directly demonstrates the W2/W3 skills being assessed.
- **Consequences**: More code than a naive pipeline; each validator is small, pure, and unit-testable (implementation-plan Phase 6).

## D-010: `.eml` file as default email draft mechanism

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Deliverable is a *draft* email to self, evidenced by screenshot or text.
- **Options**: (a) Gmail API draft (OAuth + Cloud project setup), (b) SMTP send-to-self, (c) generate a standards-compliant `.eml` file.
- **Decision**: (c) as default; (a) kept as an optional `gmail` mode with automatic fallback to `eml` (EC-MAIL-04); (b) rejected — the brief says draft, not send.
- **Why**: Zero setup, zero credentials, works offline, satisfies the deliverable exactly, and removes an OAuth failure mode from the deadline-critical path.
- **Consequences**: Some clients open `.eml` as a received message rather than editable draft — accepted (EC-MAIL-03), since the deliverable is evidence of the draft's content.

## D-011: File-based stage handoff (disk, not memory)

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: A 4-stage pipeline where the middle stages cost LLM calls; failures shouldn't force re-running everything.
- **Options**: (a) in-memory dataframe passed between functions, (b) each stage reads/writes files.
- **Decision**: (b) — each stage reads only the previous stage's file and writes its own outputs atomically.
- **Why**: Enables `--from <stage>` resume without repeating paid-in-time LLM calls; intermediate files double as inspectable debug artifacts and deliverables (`reviews.csv` is Deliverable 4 as-is).
- **Consequences**: Slightly more IO code; atomic-write convention required (conventions §2.3).

## D-012: Prompts as files, not inline strings

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Prompt iteration is expected to be the highest-churn activity (W2 skill: prompting).
- **Decision**: Every prompt is a `.txt` file in `prompts/` with `{placeholder}` variables; no prompts in Python strings.
- **Why**: Diff-able prompt history in git, editable without touching code, and reviewers can assess prompting skill by reading the folder.
- **Consequences**: A thin prompt-loading helper; format-variable mismatches surface at runtime — mitigated by the dry-run mode exercising all prompt loads.

## D-013: Hash platform review IDs instead of dropping them

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Zero-PII rule says no IDs, but the pipeline needs stable keys for dedupe and batch classification bookkeeping.
- **Options**: (a) drop IDs, use row numbers, (b) keep raw platform IDs, (c) `sha256(platform_id)[:10]`.
- **Decision**: (c).
- **Why**: (a) breaks dedupe across re-fetches and quote traceability; (b) violates the constraint — platform review IDs can be user-linkable; (c) gives stable, non-reversible keys satisfying both needs.
- **Consequences**: 10 hex chars ≈ 1 in 10^12 collision for our volumes — negligible; documented in the schema (conventions §3.1).

## D-014: Fail fast on zero reviews rather than emit empty note

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: A week could yield no reviews (wrong app ID, source outage, dead app).
- **Decision**: `PipelineError` at import when 0 reviews are in-window; low-volume weeks (<20) proceed with a "Low volume week" banner instead (EC-IMP-05/06).
- **Why**: A confidently formatted note generated from nothing would be worse than an error — it would look like insight while being noise. Loud failure protects trust in every other week's note.
- **Consequences**: Weekly automation must surface the error rather than silently skip; acceptable for a human-triggered weekly run.

## D-015: Gemini → Groq switch for primary LLM

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: The initial architecture draft proposed Google Gemini free tier (`gemini-1.5-flash`) as primary with Groq as fallback. The user then decided to use Groq.
- **Decision**: Swap: Groq primary (D-003), Gemini demoted to fallback. Rate-limit handling retuned from 4s sleep (Gemini 15 req/min) to 2s sleep (Groq ~30 req/min).
- **Why**: User preference; no architectural cost thanks to the provider-agnostic `llm_client.py` — exactly the flexibility that abstraction was designed for.
- **Consequences**: `architecture.md`, `dataflow.md`, and `conventions.md` all updated to Groq; docs must stay in sync on any future provider change.

## D-016: No database — CSV/JSON files only

- **Date**: 2026-07-15 · **Status**: ✅ Accepted
- **Context**: Weekly volumes are ~1,000 rows; history is a couple of small JSONs per week.
- **Options**: (a) SQLite, (b) flat CSV/JSON files.
- **Decision**: (b).
- **Why**: The dataset fits in memory hundreds of times over; CSV is itself a required deliverable; files are transparent for reviewers; SQLite adds schema/migration ceremony with no benefit at this scale.
- **Consequences**: WoW comparison reads dated archive files rather than querying; unbounded-but-tiny archive growth accepted (EC-OPS-07).

## D-017: Streamlit prototype link

- **Date**: 2026-07-15 · **Status**: ⏸️ Deferred
- **Context**: Deliverable 1 accepts either a prototype link or a ≤3-min demo video.
- **Decision**: Default to the demo video (screen-recording of a full run). Streamlit Community Cloud app deferred to post-core stretch time (implementation-plan §9 rung 4).
- **Why**: Video is guaranteed-cost-zero in time and risk; a hosted app adds deployment surface in a 2-day window without improving what's assessed.
- **Revisit when**: Core pipeline + tests done with ≥3 hrs of buffer left.

## D-018: Multi-label themes

- **Date**: 2026-07-15 · **Status**: ❌ Rejected
- **Context**: Considered letting a review carry multiple themes (see D-007).
- **Why rejected**: Breaks count interpretability, complicates top-3 ranking, doubles classification output complexity — for insight the note's 250-word format couldn't express anyway.
- **Revisit when**: Only if a future consumer needs per-issue (rather than per-review) analytics.

---

## D-019: Google Stitch-designed dashboard frontend ("PulseBoard")

- **Date**: 2026-07-16 · **Status**: ✅ Accepted (extends D-017)
- **Context**: User wants a high-quality UI frontend for the prototype. D-017 had deferred a Streamlit link in favor of the demo video.
- **Options**: (a) Streamlit app, (b) hand-built React dashboard, (c) Google Stitch AI-generated UI (free), exported and wired to the pipeline's JSON/CSV/MD outputs.
- **Decision**: (c) — six screens (Dashboard, Themes, Reviews, Weekly Note, Email Draft, Run Pipeline) defined as screen-wise Stitch prompts in `Docs/stitch-prompts.md`, sharing an embedded design system (light theme, PhonePe purple #5F259F, Inter).
- **Why**: Stitch is free (D-001 holds), produces polished visuals fast within the deadline, and each prompt embeds the full design system since Stitch has no cross-prompt memory.
- **Consequences**: The generated frontend is static until wired to `theme_counts.json` / `reviews_themed.csv` / `weekly_note_*.md`; demo video remains the fallback deliverable if wiring doesn't fit the timeline.

## New Decisions (append below)

> Template:
>
> ```
> ## D-NNN: <title>
> - **Date**: YYYY-MM-DD · **Status**: ✅/🔄/⏸️/❌
> - **Context**: what situation forced a choice
> - **Options**: what was considered
> - **Decision**: what was chosen
> - **Why**: the deciding factors
> - **Consequences**: what we accept as a result (link edge cases / docs affected)
> ```
