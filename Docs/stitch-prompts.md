# Google Stitch Prompts — App Review Insights Analyser Frontend (Premium Edition)

> One highly detailed prompt per screen, in build order. Paste each into Google Stitch (stitch.withgoogle.com) as a separate screen of the same project. The **full design system is embedded in every prompt** — Stitch has no cross-prompt memory, so repetition is what keeps all six screens looking like one premium product.

## Design Language: "PulseBoard Premium"

- Mood: premium fintech intelligence tool — think Linear meets Stripe Dashboard meets Bloomberg terminal elegance
- **Dark luxe theme**: near-black canvas #0B0B10, elevated surfaces #141420, cards #1A1A28 with 1px inner border rgba(255,255,255,0.06) and 20px radius
- **Signature gradient**: purple → violet (#7C3AED → #A78BFA) used for primary buttons, active states, chart fills, and a subtle radial glow behind hero numbers
- Accents: mint green #34D399 (positive), amber #FBBF24 (caution), rose #FB7185 (negative), all with soft 20% glows
- Typography: Inter — 28px/semibold page titles with -0.02em tracking, 15px body #E5E7EB, 12px uppercase labels with 0.08em tracking in #9CA3AF, tabular numerals for all metrics
- Depth: layered soft shadows, frosted-glass top bar (backdrop blur), gradient borders on featured cards
- Details: 8pt spacing grid, 24–32px card padding, pill-shaped chips, thin 1.5px stroke icons (Lucide style), smooth rounded chart corners

---

## Screen 1 — Dashboard (Weekly Pulse Overview)

```
Design a premium desktop analytics dashboard, 1440px wide, for "PulseBoard" — an elite fintech intelligence tool that turns PhonePe app store reviews into weekly executive insights. Aesthetic: Linear meets Stripe Dashboard. Dark luxe theme: near-black #0B0B10 canvas, elevated cards #1A1A28 with 20px radius, 1px rgba(255,255,255,0.06) inner borders, layered soft shadows. Signature purple→violet gradient (#7C3AED→#A78BFA) for primary elements. Inter font, tabular numerals, 12px uppercase tracking-wide labels in #9CA3AF, 15px body in #E5E7EB.

Left sidebar, 240px, #141420, frosted glass feel: "PulseBoard" wordmark with a small gradient pulse-wave logo, then nav items with thin 1.5px stroke icons — Dashboard (active: gradient pill background with soft glow), Themes, Reviews, Weekly Note, Email Draft, Run Pipeline. Bottom of sidebar: a mini card "Free tier · quotas reset daily" with a tiny progress ring at 42%.

Top bar, frosted glass with backdrop blur: breadcrumb "Insights / Weekly Pulse", a search field with ⌘K shortcut hint, a date-range chip "May 6 – Jul 16, 2026", and a gradient primary button "Run New Week" with subtle glow.

Hero row: 4 stat cards with big 32px tabular numbers and tiny sparklines.
1. "TOTAL REVIEWS" 2,100 with mint "+12% WoW" pill and a soft radial purple glow behind the number
2. "AVG RATING" 4.31★ with a micro 5-bar rating histogram
3. "PROBLEM REVIEWS" 207 (9.9%) in amber with a warning triangle chip
4. "ACTIVE THEMES" 5 with five tiny colored dots

Middle row, 2 columns (60/40):
Left card "Theme Distribution" with a horizontal bar chart, rounded bar caps, gradient purple fills fading to transparent, counts right-aligned in tabular numerals: General Praise & Sentiment 1,788 · App Performance & Compatibility 117 · Features & Usability 105 · Payment Failures 64 · Data Security & Privacy 26. Hover state shown on the second bar with a floating glass tooltip "117 reviews · 2.84★ avg".
Right card "Sentiment Health" with a large 140px donut gauge showing 85% positive in gradient purple with a glowing end cap, center label "4.31★", and a mini legend: Positive 85% mint · Neutral 5% gray · Negative 10% rose.

Bottom row: featured card with a thin gradient border, "Latest Weekly Note — Jul 16, 2026", three green check chips "245/250 words · 3 quotes verified · PII clean", a 2-line elegant serif-italic pull-quote preview "Payment failures rose to 64 reports this week…", and a ghost button "Open note →" plus gradient button "Draft Email".
```

## Screen 2 — Themes Explorer

```
Design a premium desktop "Themes" screen, 1440px, for "PulseBoard" — an elite fintech intelligence tool for PhonePe app review insights. Aesthetic: Linear meets Stripe Dashboard. Dark luxe: #0B0B10 canvas, cards #1A1A28, 20px radius, 1px rgba(255,255,255,0.06) borders, purple→violet gradient (#7C3AED→#A78BFA) accents with soft glows, Inter font, tabular numerals, uppercase 12px tracked labels in #9CA3AF. Left 240px sidebar #141420 with gradient-pill active state: Dashboard, Themes (active), Reviews, Weekly Note, Email Draft, Run Pipeline. Frosted-glass top bar with breadcrumb "Insights / Themes".

Page header: 28px title "Themes", caption "Max 5 — auto-discovered by LLM each week", a premium segmented control "Auto-discover | Reuse legend" (first selected with gradient fill), and a ghost icon-button "Regenerate ↻".

Bento grid of 5 theme cards, asymmetric premium layout: one large featured card (2x width) + four standard cards. Every card: theme name 18px semibold, one-line definition in #9CA3AF, a huge 36px tabular review count with soft glow, star rating chip (mint ≥4★, amber 2.5–4★, rose <2.5★), a WoW delta pill, and an area sparkline with gradient fill fading to transparent.

Featured card: "General Praise & Sentiment" — Users expressing general sentiment without specific topics · 1,788 reviews · 4.55★ mint chip · "+9% WoW" mint pill · large smooth sparkline, plus two elegant italic sample quotes with thin left gradient rules: "Best UPI app, my mom uses it easily without any help" and "Simply super, fast and secure every single time".

Standard cards:
"App Performance & Compatibility" 117 · 2.84★ amber · "−4% WoW" mint pill
"Features & Usability" 105 · 4.37★ mint · "+6% WoW"
"Payment Failures" 64 · 2.53★ rose · "+15% WoW" rose pill with small alert glow
"Data Security & Privacy" 26 · 2.35★ rose · "new" purple pill

Footer strip in glass style: "Legend generated Jul 16, 2026 · llama-3.3-70b-versatile · 1 discovery call" with a tiny model chip icon.
```

## Screen 3 — Reviews Explorer

```
Design a premium desktop "Reviews" data-table screen, 1440px, for "PulseBoard" — an elite fintech intelligence tool for PhonePe app review insights. Aesthetic: Linear meets Stripe Dashboard. Dark luxe: #0B0B10 canvas, surfaces #1A1A28, 20px radius cards, 1px rgba(255,255,255,0.06) borders, purple→violet gradient (#7C3AED→#A78BFA), Inter, tabular numerals. Left 240px sidebar #141420: Dashboard, Themes, Reviews (active gradient pill), Weekly Note, Email Draft, Run Pipeline. Frosted-glass top bar, breadcrumb "Insights / Reviews".

Header: 28px "Reviews" title beside a glowing mint shield badge "PII SCRUBBED — usernames never stored", caption "2,100 reviews · hashed IDs · regex-redacted at ingestion". Right side: elegant search input with ⌘F hint and an "Export CSV" ghost button.

Filter bar of premium pill chips with subtle borders: "All stores ▾", "All themes ▾", star selector showing ★★★★★ outlines with 1–2 stars filled rose, date chip "May 6 – Jul 16", and an active filter pill "Payment Failures ✕" in gradient. 

Data table in a full-width card, generous 56px rows, hairline dividers rgba(255,255,255,0.05):
Columns: REVIEW (2-line truncated), STORE (small Play triangle / Apple logo chip), RATING (stars — rose for 1–2★, mint for 4–5★), THEME (translucent lavender pill), DATE (tabular, right-aligned).
Rows with realistic payments-app content:
1. "Payment stuck for 3 days, money debited but not credited back to my account" · Play · 1★ rose · Payment Failures · Jul 15
2. "Best UPI app I've used, my mom operates it easily without my help" · Play · 5★ mint · General Praise · Jul 15
3. "App crashes on Android 12 every time after the latest update" · Play · 2★ rose · App Performance · Jul 14
4. "Please add a dark mode and transaction search filters" · App Store · 4★ mint · Features & Usability · Jul 14
5. "Contacted support at [REDACTED] and still no response about my refund" · Play · 1★ rose · Payment Failures · Jul 13 — the [REDACTED] token styled as a small dark chip with a shield icon and hover tooltip "PII removed at ingestion"
6. "Worried about the new data sharing policy, want my account deleted" · App Store · 2★ rose · Data Security · Jul 12
Row 1 shown in hover state: slightly elevated with a soft purple left edge glow.

Footer: "1–25 of 2,100" with premium pagination pills and a rows-per-page dropdown.
```

## Screen 4 — Weekly Note

```
Design a premium desktop "Weekly Note" screen, 1440px, for "PulseBoard" — an elite fintech intelligence tool for PhonePe app review insights. Aesthetic: Linear meets Stripe. Dark luxe: #0B0B10 canvas, cards #1A1A28, 20px radius, purple→violet gradient (#7C3AED→#A78BFA), Inter font. Left 240px sidebar #141420: Dashboard, Themes, Reviews, Weekly Note (active gradient pill), Email Draft, Run Pipeline. Frosted-glass top bar, breadcrumb "Insights / Weekly Note".

Two columns. Left rail, 300px: "NOTE HISTORY" label, then a vertical timeline with gradient connector line and dated entries — "Jul 16, 2026" active with gradient dot, glow, and chips "245/250 · ✓✓✓"; below it "Jul 9, 2026" and "Jul 2, 2026" in muted style with their own mini badges. At the bottom a subtle "Week-over-week: Payment Failures +15%" insight chip in rose.

Right main area: the note presented as a luxurious light-mode document card — warm white #FDFDFB paper with 24px radius floating on the dark canvas with a deep soft shadow and a thin gradient border, like a premium printed report. Document content in dark ink #1F2937:
Serif-accented title "Weekly App Review Pulse — week ending 2026-07-16", subtitle "2,100 reviews analyzed · Play Store + App Store · last 10 weeks".
Section "TOP 3 THEMES" with three rows: App Performance & Compatibility — 117 reviews · 2.84★, Features & Usability — 105 · 4.37★, Payment Failures — 64 · 2.53★, each with a small colored square bullet.
Section "WHAT USERS ARE SAYING": three elegant italic quotes with hanging quotation marks and small purple theme tags.
Section "RECOMMENDED ACTIONS": numbered 1–3 in gradient-filled circles with concise action text.

Floating above the document, a glass validation bar with three glowing mint check chips: "245 / 250 words", "3 quotes verified verbatim", "PII scan clean" — plus a small gray chip "llama-3.3-70b".

Top-right action cluster: ghost buttons "Copy Markdown" and "Export PDF" with icons, and a gradient primary button "Draft Email →" with soft glow.
```

## Screen 5 — Email Draft

```
Design a premium desktop "Email Draft" screen, 1440px, for "PulseBoard" — an elite fintech intelligence tool for PhonePe app review insights. Aesthetic: Linear meets Stripe. Dark luxe: #0B0B10 canvas, cards #1A1A28, 20px radius, purple→violet gradient (#7C3AED→#A78BFA), Inter. Left 240px sidebar #141420: Dashboard, Themes, Reviews, Weekly Note, Email Draft (active gradient pill), Run Pipeline. Frosted-glass top bar, breadcrumb "Insights / Email Draft".

Center-left (fluid): an email preview rendered as a premium mail-client card. Header block on slightly lighter surface #22222E with monospace-styled meta rows: "To  bipsdsn@gmail.com", "From  bipsdsn@gmail.com", "Subject  Weekly App Review Pulse — 2026-07-16", plus two pills: gradient "DRAFT" and outlined mint "never auto-sent". A thin gradient divider, then the email body on a warm white #FDFDFB inset panel rendering the note as refined HTML: h2 title, "Top 3 Themes" bullets with counts and stars (App Performance 117 · 2.84★, Features & Usability 105 · 4.37★, Payment Failures 64 · 2.53★), "What Users Are Saying" with 3 italic quotes tagged with theme labels, "Recommended Actions" numbered list. Realistic, elegant typography.

Right rail, 320px, two stacked cards:
1. "DELIVERY" — radio list: ".eml file (zero setup)" selected with gradient radio and caption "opens as a draft in any mail client", "Gmail draft via OAuth" disabled with a lock icon and "optional" tag. Below, a large gradient button "Download .eml" with glow and a ghost button "Regenerate from latest note ↻".
2. "EVIDENCE CHECKLIST" — three checklist rows with mint checks: "Draft addressed to self", "Note embedded (plain + HTML)", "UTF-8 ★ ₹ — rendering verified", plus a caption "Screenshot this draft for Deliverable 3" with a tiny camera icon.
```

## Screen 6 — Run Pipeline

```
Design a premium desktop "Run Pipeline" mission-control screen, 1440px, for "PulseBoard" — an elite fintech intelligence tool for PhonePe app review insights. Aesthetic: Linear meets Stripe meets mission control. Dark luxe: #0B0B10 canvas, cards #1A1A28, 20px radius, purple→violet gradient (#7C3AED→#A78BFA) with glows, Inter, tabular numerals. Left 240px sidebar #141420: Dashboard, Themes, Reviews, Weekly Note, Email Draft, Run Pipeline (active gradient pill). Frosted-glass top bar, breadcrumb "Automation / Run Pipeline".

Hero card: a horizontal 4-stage pipeline visualization with connected nodes and an animated gradient flow line — "Import" (completed: mint check node, caption "2,100 reviews · 1,600 Play + 500 App Store"), "Group Themes" (completed: mint check, caption "5 themes · 84 LLM calls"), "Generate Note" (active: pulsing gradient node with glow ring, caption "Writing note… llama-3.3-70b"), "Draft Email" (pending: hollow gray node). Under the nodes, a slim gradient progress bar at 65% with "~40s remaining" in tabular numerals.

Below, two columns (55/45):
Left card "LIVE LOG": terminal-style panel on #0E0E15 with JetBrains Mono 13px lines, timestamps in #6B7280, log levels color-coded — "00:12:40 INFO group: classified 2100/2100", "00:12:41 INFO group: theme counts written", "00:12:41 INFO note: top themes ['App Performance', 'Features & Usability', 'Payment Failures']", "00:12:42 WARN llm: 70B quota low — fallback armed", "00:12:44 INFO note: 245 words, 3 quotes verified ✓". A blinking gradient cursor on the last line. Small "Auto-scroll" toggle top-right.

Right card "RUN CONFIGURATION": premium form — a gradient-filled slider "Analysis window: 10 weeks" with range marks 8–12, an elegant toggle "Reuse theme legend" (on, gradient), two read-only model chips "llama-3.3-70b-versatile · quality" and "llama-3.1-8b-instant · volume", an email field "bipsdsn@gmail.com" with a verified mint check, then a large gradient primary button "Run Full Pipeline" with strong glow and a subtle ghost button "Dry Run" beside it.

Footer glass strip: "≈86 LLM calls per run · free tier · daily quotas reset on a rolling 24h window" with a small info icon and a mini quota ring at 42%.
```

---

## Usage Tips

1. Build screens in the order above — the Dashboard establishes the visual language.
2. If any screen drifts, append: "Match the exact visual style of the Dashboard screen: #0B0B10 canvas, #1A1A28 cards, purple→violet gradient #7C3AED→#A78BFA, Inter, 20px radii" and regenerate.
3. The light "paper" document inside Screens 4–5 is intentional — a warm-white report floating on the dark canvas reads premium and mirrors the real deliverable.
4. After generating: "Copy to Figma" for fine-tuning, or export code and wire it to the pipeline outputs (`theme_counts.json`, `reviews_themed.csv`, `weekly_note_*.md`, `email_draft.eml`).
