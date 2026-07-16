# Deployment Guide: App Review Insights Analyser

> Frontend (PulseBoard static screens) → **Vercel** · Backend (pipeline + API) → **Railway**. Both free tiers. All configuration files referenced below already exist in the repo.

## Architecture After Deployment

```
┌──────────────────────────┐         ┌─────────────────────────────────┐
│  VERCEL (free)           │  HTTPS  │  RAILWAY (free trial/hobby)     │
│  PulseBoard static UI    │ ──────▶ │  FastAPI server (server.py)     │
│  6 screens + index.html  │         │  ├─ GET  /api/theme-counts      │
│  folder:                 │         │  ├─ GET  /api/note              │
│  stitch_pulseboard_…     │         │  ├─ GET  /api/reviews           │
└──────────────────────────┘         │  ├─ GET  /api/email-draft       │
                                     │  └─ POST /api/run  (token-gated)│
                                     │  Runs the pipeline on demand:   │
                                     │  Import → Scrub → Group → Note  │
                                     │  → Email draft                  │
                                     └───────────────┬─────────────────┘
                                                     │ Groq API (free tier)
                                                     ▼
                                          llama-3.3-70b / llama-3.1-8b
```

## Prerequisites

- GitHub account (both platforms deploy from GitHub repos)
- Vercel account (free) — vercel.com
- Railway account (free trial / hobby) — railway.app
- Your Groq API key (**rotate the old one first** at console.groq.com — the current key was shared in chat)

## Step 0 — Push to GitHub (two repos or one monorepo)

Recommended: one repo with both folders.

```bash
cd "c:\Users\kabideba\Downloads\Ai Agent"
git init
git add app-review-insights stitch_pulseboard_premium_intelligence_dashboard Docs
git commit -m "feat: App Review Insights Analyser — pipeline, API, and PulseBoard UI"
# create an empty repo on github.com, then:
git remote add origin https://github.com/<you>/app-review-insights.git
git push -u origin main
```

**Safety check before pushing** — these must NOT be in the repo (already gitignored, verify anyway):

```bash
git status --ignored | findstr .env        # .env must show as ignored
```

Never commit: `.env` (Groq key), `data/raw/`, full `data/*.csv` dumps.

## Step 1 — Backend on Railway

1. railway.app → **New Project → Deploy from GitHub repo** → pick your repo
2. **Settings → Root Directory** → `app-review-insights`
   (Railway auto-detects Python via `requirements.txt`; `railway.json` + `Procfile` supply the start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`)
3. **Variables** — add these three:

   | Variable | Value | Purpose |
   |---|---|---|
   | `GROQ_API_KEY` | your (rotated) key | LLM calls |
   | `RUN_TOKEN` | any long random string | protects POST /api/run |
   | `FRONTEND_ORIGIN` | your Vercel URL (add after Step 2) | CORS lock-down |

4. Deploy → **Settings → Networking → Generate Domain** → note the URL, e.g. `https://app-review-insights-production.up.railway.app`
5. **First run** (populates outputs on the server — takes ~10–15 min for classification):

   ```bash
   curl -X POST https://<railway-url>/api/run -H "X-Run-Token: <your RUN_TOKEN>"
   curl https://<railway-url>/api/run-status          # poll until running:false
   curl https://<railway-url>/api/theme-counts        # verify data
   ```

### Security notes (important)

- **Read endpoints are public** but serve only PII-free artifacts (that guarantee is enforced by the pipeline's scrub boundary, not by the API).
- **POST /api/run is token-protected** because each run consumes Groq quota. Without `RUN_TOKEN` set, the endpoint returns 503 and nothing can trigger runs.
- Set `FRONTEND_ORIGIN` to your exact Vercel URL after Step 2 to lock CORS down from the default `*`.

### Railway free-tier caveats

- **Ephemeral filesystem**: outputs (`output/`, `data/`) are wiped on redeploy/restart. Re-trigger `/api/run` after each deploy, or attach a Railway Volume mounted at `/app/data` + `/app/output` if you want persistence.
- Free trial has limited monthly hours — fine for the challenge demo window.

## Step 2 — Frontend on Vercel

1. vercel.com → **Add New → Project** → import the same GitHub repo
2. **Root Directory** → `stitch_pulseboard_premium_intelligence_dashboard`
3. Framework preset: **Other** (it's plain static HTML — no build step, `index.html` redirects to the dashboard)
4. Deploy → you get `https://<project>.vercel.app`

Clean URLs are configured in `vercel.json`:

| URL | Screen |
|---|---|
| `/` | redirects to Dashboard |
| `/dashboard` | Weekly Pulse overview |
| `/themes` | Themes explorer |
| `/reviews` | Reviews explorer |
| `/note` | Weekly note report |
| `/email` | Email draft preview |
| `/pipeline` | Run pipeline mission control |

5. Go back to Railway and set `FRONTEND_ORIGIN=https://<project>.vercel.app`

## Step 3 — Verify End to End

```bash
# frontend up
curl -s -o NUL -w "%{http_code}" https://<project>.vercel.app/dashboard     # 200
# backend healthy
curl https://<railway-url>/                                                  # {"status":"ok"}
# real data flowing
curl https://<railway-url>/api/theme-counts                                  # totals JSON
```

Then open the Vercel URL in a browser and click through all six screens via the sidebar.

## What Is (Deliberately) Not Wired Yet

The PulseBoard screens display **real but static** data (baked in from the Jul 16 run). They do not fetch from the Railway API live. This is intentional for the deadline: the prototype link + working API + demo video fully satisfy the deliverables. To wire them later, replace the hardcoded numbers with `fetch('https://<railway-url>/api/theme-counts')` calls — the API shapes match the UI one-to-one.

## Submission Mapping

| Deliverable | After deployment |
|---|---|
| Working prototype link | Vercel URL (UI) + Railway URL (API) |
| Weekly note | `/api/note` on Railway, or `output/weekly_note_*.md` |
| Email draft evidence | `/api/email-draft` download → open → screenshot |
| Reviews CSV | `data/sample_reviews.csv` in the repo |
| README | `app-review-insights/README.md` |

## Troubleshooting

| Symptom | Fix |
|---|---|
| Railway build fails on pandas | Ensure Root Directory is `app-review-insights` so `requirements.txt` (pandas 2.2.3) is found |
| `/api/*` returns 404 "No run yet" | Trigger `POST /api/run` with the token; poll `/api/run-status` |
| `/api/run` returns 503 | `RUN_TOKEN` variable not set on Railway |
| `/api/run` returns 401 | Header must be exactly `X-Run-Token: <value>` |
| Run fails with Groq 429 | Daily token quota hit — wait for the rolling 24 h window or switch model in `config.yaml` |
| CORS errors in browser console | `FRONTEND_ORIGIN` must exactly match the Vercel URL (https, no trailing slash) |
| Screens 404 on Vercel | Root Directory must be the stitch folder, not the repo root |
