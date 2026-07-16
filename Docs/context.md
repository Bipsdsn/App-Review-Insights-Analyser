# Context: App Review Insights Analyser

## Background

This project is part of an AI Agent challenge (LIP challenge series). It builds on the product selected in the previous challenge (LIP challenge 4) and requires turning raw app store reviews into actionable weekly insights using LLMs and workflow automation.

## Target Users

| Audience | What They Get |
|---|---|
| Product / Growth Teams | Understand what to fix next based on user pain points |
| Support Teams | Know what users are saying and can acknowledge trends |
| Leadership | Quick weekly health pulse without reading raw reviews |

## Input Data

- **Source**: Public review exports from Apple App Store and Google Play Store
- **Window**: Last 8–12 weeks of reviews
- **Fields per review**: rating, title, text, date
- **Format**: CSV (sample or redacted data is acceptable for submission)
- **Restriction**: No scraping behind logins; public exports only

## Processing Pipeline

### Stage 1: Import
Load and normalize reviews from both stores into a single dataset. Filter to the 8–12 week window. Strip any PII (usernames, emails, IDs) at ingestion.

### Stage 2: Theme Grouping
Use an LLM to classify each review into one of at most 5 themes. Example theme legend for a fintech product:

- Onboarding
- KYC / Verification
- Payments
- Statements
- Withdrawals

Themes should be adapted to the actual product and review content.

### Stage 3: Weekly Note Generation
LLM-generated one-page note with strict structure:

- **Top 3 themes** — ranked by volume/severity, with brief summaries
- **3 user quotes** — real, verbatim (PII-free), chosen to illustrate the top themes
- **3 action ideas** — concrete, prioritized suggestions for the product team

Formatting rules: scannable layout (headers, bullets), ≤250 words total.

### Stage 4: Email Draft
Draft an email containing the weekly note and send it to self/alias. Evidence via screenshot or text of the draft.

## Hard Constraints

1. **Max 5 themes** — forces prioritization
2. **≤250 words per note** — forces conciseness and scannability
3. **Zero PII** — no usernames, emails, or IDs anywhere in outputs or artifacts
4. **Public data only** — no authenticated scraping

## LLM / Prompting Considerations (W2)

- **Summarization**: condense dozens of reviews per theme into 1–2 sentence summaries
- **Quote selection**: pick representative, verbatim quotes that carry emotional weight without PII
- **Tone control**: professional, neutral pulse-report tone suitable for leadership

## Automation Considerations (W3)

- Pipeline must be **re-runnable for a new week** with minimal effort (documented in README)
- Steps: import → group → generate note → draft email, ideally chained end-to-end
- Consider parameterizing the date window so each weekly run picks up fresh reviews

## Deliverables Checklist

- [ ] Working prototype link or ≤3-min demo video
- [ ] Latest one-page weekly note (PDF/Doc/MD)
- [ ] Email draft (screenshot or text)
- [ ] Reviews CSV used (sample/redacted fine)
- [ ] README with re-run instructions and theme legend

## Timeline

- **Submission deadline**: Jul 17, 11:59:00 PM (Asia/Calcutta) — 2 days from now
