# Problem Statement: App Review Insights Analyser

## The Problem

Product, growth, support, and leadership teams struggle to keep up with the steady stream of user reviews on the App Store and Play Store. Reviews contain valuable signals — recurring complaints, feature requests, and sentiment shifts — but they arrive as unstructured, high-volume text scattered across two platforms. Manually reading, categorizing, and summarizing them every week is slow, inconsistent, and rarely done.

As a result:

- **Product/Growth teams** miss emerging issues and don't know what to fix next
- **Support teams** lack a clear picture of what users are saying and can't acknowledge trends proactively
- **Leadership** has no quick, reliable weekly health pulse of user sentiment

## The Solution

Build an automated AI workflow that turns recent App Store + Play Store reviews into a **one-page weekly pulse note**, then drafts an email delivering it.

### Core Workflow

```
Import Reviews → Group into Themes → Generate Weekly Note → Draft Email
```

1. **Import** — Ingest reviews from the last 8–12 weeks (rating, title, text, date) from public review exports
2. **Group** — Cluster reviews into a maximum of 5 themes (e.g., onboarding, KYC, payments, statements, withdrawals)
3. **Generate** — Produce a scannable, ≤250-word weekly note containing:
   - Top 3 themes
   - 3 real user quotes
   - 3 action ideas
4. **Deliver** — Draft an email containing the weekly note (sent to self/alias)

## Constraints

| Constraint | Detail |
|---|---|
| Data source | Public review exports only — no scraping behind logins |
| Themes | Maximum 5 |
| Note length | ≤250 words, scannable format |
| Privacy | No PII — no usernames, emails, or IDs in any artifact |

## Success Criteria (Deliverables)

1. Working prototype link or ≤3-minute demo video
2. Latest one-page weekly note (PDF/Doc/MD)
3. Email draft (screenshot or text)
4. Reviews CSV used (sample/redacted acceptable)
5. README covering:
   - How to re-run for a new week
   - Theme legend

## Skills Demonstrated

- **W2 — LLMs & Prompting**: summarization, quote selection, tone control
- **W3 — AI Workflow Automations**: import → group → generate note → draft email pipeline

## Deadline

Jul 17, 11:59:00 PM (Asia/Calcutta)
