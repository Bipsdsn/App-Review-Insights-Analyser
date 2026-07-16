# Evals (Living Document): App Review Insights Analyser

> **Living document** — defines how we measure whether the pipeline's LLM stages actually work well, not just whether they run. Companion to `architecture.md`, `conventions.md`, `edgecases.md`, and `decisions.md`.
>
> **How to use**: Run the relevant evals after any prompt change, model change, or batch-size change. Record results in the Run Log (§8). Add new eval cases as failures are discovered — every production bug should become an eval case.
>
> **Principle**: Hard constraints get automated pass/fail checks (already enforced in code per D-009). Evals here measure the *quality* dimensions code can't assert — classification accuracy, quote quality, note usefulness, tone.

**Last updated**: 2026-07-15

---

## 1. What We Evaluate (and What We Don't)

| Layer | Property | How measured | Where |
|---|---|---|---|
| Enforced in code | ≤5 themes, ≤250 words, quotes verbatim, zero PII, valid JSON | Deterministic validators + unit tests | pipeline + `tests/` |
| **Evaluated here** | Theme quality, classification accuracy, quote selection quality, note usefulness, tone | Golden sets + rubrics + spot checks | this doc |
| Not evaluated | Latency, cost | Irrelevant at free-tier scale (~43 calls, ~3 min) | — |

The split matters: validators prevent shipping a *broken* note; evals prevent shipping a *useless* one.

---

## 2. Eval Assets

```
evals/
├── golden_reviews.csv        # ~60 hand-picked scrubbed reviews, diverse + tricky
├── golden_labels.csv         # review_id → expected theme (human-assigned)
├── pii_probes.csv            # adversarial PII strings that must be redacted
├── quote_pool_cases.json     # inputs with known good/bad quote candidates
└── run_log.md                # (or §8 below) dated results per eval run
```

- **golden_reviews.csv** is built once during Phase 2 from real imported data: ~60 reviews covering every theme, both stores, rating extremes, multilingual, sarcasm, multi-issue, and emoji-heavy cases.
- Golden labels are assigned by the builder (single annotator — acceptable for this scale; note ambiguous cases with a `?` flag and exclude them from strict accuracy).

---

## 3. EV-THM: Theme Grouping Evals

### EV-THM-01 — Classification accuracy vs golden labels

- **Method**: Run the classification prompt over `golden_reviews.csv`; compare to `golden_labels.csv`.
- **Metric**: % exact match (excluding `?`-flagged ambiguous rows).
- **Target**: ≥ 85% · **Red line**: < 75% → revise prompt or legend before shipping the week's note.
- **Automation**: `python -m evals.run_classification` (uses the real Groq client; ~3 calls).

### EV-THM-02 — Classification stability (temperature 0.0 determinism)

- **Method**: Classify the golden set twice in the same session; diff the label maps.
- **Metric**: % identical labels across runs.
- **Target**: ≥ 98%. Instability → tighten prompt or reduce batch size (revisit D-008).

### EV-THM-03 — Legend quality rubric (manual, per discovery run)

Score the discovered legend 1–5 on each; record in Run Log:

| Criterion | 5 looks like | 1 looks like |
|---|---|---|
| Topic-based | "KYC / Verification" | "Bad experience" (sentiment, not topic — EC-THM-02) |
| Mutually exclusive | little overlap between definitions | "Payments" + "Transactions" both present |
| Coverage | `Other` < 10% after classification | `Other` > 15% (EC-THM-05 guard fires) |
| Actionable granularity | a PM could own each theme | themes too broad to act on |

- **Target**: every criterion ≥ 4 before the legend is accepted for the week.

### EV-THM-04 — Multi-issue review handling

- **Method**: 8–10 golden reviews deliberately mention two issues; check the assigned label matches the *dominant* issue per the human label.
- **Target**: ≥ 7/10 — confirms the "dominant issue" instruction works (D-007).

---

## 4. EV-PII: PII Scrub Evals

### EV-PII-01 — Adversarial probe set

- **Method**: `pii_probes.csv` holds ~40 strings that MUST be redacted: emails (subaddressed, odd TLDs), Indian phone formats, Aadhaar/PAN patterns, @handles, long IDs, tokenized URLs — plus ~20 strings that MUST NOT be redacted (₹ amounts, "3 days", "version 2.4.1", short OTP mentions).
- **Metric**: recall on must-redact (target **100%** — this is the non-negotiable constraint) and precision on must-keep (target ≥ 95%; over-redaction hurts quote quality but not compliance).
- **Automation**: pure unit test, runs in `pytest` (no LLM) — this is the one eval that is also a hard gate.
- **Rule**: any probe failure blocks release; any PII found later in an artifact becomes a new probe row (living growth path).

### EV-PII-02 — End-artifact sweep

- **Method**: After a full pipeline run, regex-sweep `reviews.csv`, the note, and the `.eml` for `@`, 8+ digit runs, and phone patterns; then a 2-minute human skim of the note for prose names (EC-PII-03 residual risk).
- **Cadence**: every weekly run, and mandatory before submission (implementation-plan Phase 7).

---

## 5. EV-NOTE: Weekly Note Evals

### EV-NOTE-01 — Structural conformance (automated, doubles as validator)

Checklist per generated note: title w/ week-ending date · exactly top-N themes with count + avg★ · exactly 3 quotes, all substring-verified · exactly 3 numbered actions · ≤250 words · no preamble text.
- **Target**: 100% (any miss is a validator bug — fix the code, add a test).

### EV-NOTE-02 — Quote selection quality rubric (manual)

Score each of the 3 quotes 1–5:

| Criterion | Good quote | Bad quote |
|---|---|---|
| Representative | echoes the theme's most common complaint | edge-case rant |
| Vivid | concrete, specific, emotional weight | generic ("app is bad") |
| Self-contained | understandable without context | needs the full review to parse |
| Clean | no `[REDACTED]`, no names, sensible length | truncated mid-thought |

- **Target**: average ≥ 4 across the 3 quotes. Persistent low scores → tune quote-pool prefilter (length/rating rules) before touching the prompt.

### EV-NOTE-03 — Action idea quality rubric (manual)

Score each of the 3 actions 1–5: **specific** (names the flow/feature, not "improve quality") · **grounded** (traceable to a top-3 theme's evidence) · **feasible** (a team could start this week) · **prioritized** (ordered by impact).
- **Target**: average ≥ 4. This is the highest-leverage output for the Product/Growth audience.

### EV-NOTE-04 — Tone check (manual)

- **Method**: Read the note as if you were leadership. Flags: hype words ("amazing", "disaster"), blame framing, adjectives where numbers should be, paragraphs > 2 sentences.
- **Target**: zero flags (conventions §9 style guide is the rubric).

### EV-NOTE-05 — Faithfulness / no-hallucination check

- **Method**: Every number in the note must appear in the code-injected stats block; every claim must be traceable to a theme summary or quote. Diff numbers manually (they're few).
- **Target**: 100%. Any invented statistic → strengthen the "copy stats verbatim" prompt instruction and add the failing case here (EC-NOTE-07).

### EV-NOTE-06 — A/B on prompt changes

- **Method**: When changing `weekly_note.txt`, generate notes with old and new prompts from the *same* themed data; compare side-by-side on EV-NOTE-02/03/04 rubrics before adopting.
- **Rule**: prompt changes without an A/B note in the Run Log don't ship.

---

## 6. EV-E2E: End-to-End Weekly Smoke Eval

Run on every real weekly execution (~5 minutes of human time):

| # | Check | Pass condition |
|---|---|---|
| 1 | Pipeline exit code | 0 |
| 2 | Review volume sanity | count within ±50% of last week (else investigate source health) |
| 3 | `Other` bucket | < 15% |
| 4 | EV-NOTE-01 structural checklist | all green |
| 5 | 2-min PII skim (EV-PII-02) | nothing found |
| 6 | Gut check: "Would I send this to a VP?" | yes |

Record a one-line result in the Run Log. Two consecutive failures of the same check → open a decision entry in `decisions.md`.

---

## 7. Regression Policy (What Makes This "Living")

1. **Every escaped defect becomes an eval case**: a misclassified review → golden set row; a leaked PII pattern → probe row; a bad quote → quote_pool case.
2. **Prompt/model/batch changes require re-running** the affected eval group before merging (EV-THM for classification changes, EV-NOTE for note prompt changes, all groups for model swaps).
3. **Targets are versioned here** — if a target changes (e.g., accuracy 85% → 90%), record why in `decisions.md` and update §3–6.
4. Golden sets are **append-mostly**: relabel only with a note in the Run Log explaining why.

---

## 8. Run Log (append below)

> Template: `| date | eval(s) run | model/prompt version | result | action taken |`

| Date | Evals | Version | Result | Action |
|---|---|---|---|---|
| _(none yet — first entries land in Phase 2/3 of the implementation plan)_ | | | | |

---

## 9. Eval Backlog (ideas, not yet built)

- [ ] EV-THM-05: confusion matrix per theme pair to spot systematic mix-ups (build if accuracy < target)
- [ ] EV-NOTE-07: readability score (e.g., grade level) as a proxy for scannability
- [ ] EV-PII-03: seeded synthetic PII injected into a test run end-to-end to prove boundary integrity
- [ ] EV-THM-06: week-over-week legend drift metric when `--reuse-legend` is off
- [ ] LLM-as-judge scoring for EV-NOTE-02/03 to reduce manual rubric time (only if weekly runs continue past the challenge)
