"""Stage 1: Import reviews from Play Store, App Store RSS, and manual CSVs.

Raw source data (with usernames) exists in memory only — every frame is
routed through pii_scrub before merging and writing (dataflow.md stage 1.5).
Writes data/reviews.csv atomically.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from src import pii_scrub
from src.errors import PipelineError

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
OUTPUT_CSV = ROOT / "data" / "reviews.csv"
RAW_DIR = ROOT / "data" / "raw"

CANONICAL_COLUMNS = ["review_id", "store", "rating", "title", "text", "date"]
MAX_TEXT_CHARS = 2000  # EC-IMP-18
RSS_MAX_PAGES = 10
# High-volume apps (PhonePe) have far more reviews in-window than a weekly
# pulse needs. Cap the Play Store fetch at the newest N rows — a large,
# recent sample that also keeps the LLM classification budget intact.
MAX_PLAY_REVIEWS = 1500

# Manual CSV best-effort column aliases (EC-IMP-10)
COLUMN_ALIASES = {
    "text": ["text", "content", "body", "review", "review_text", "comment"],
    "title": ["title", "headline", "subject"],
    "rating": ["rating", "score", "stars", "star_rating"],
    "date": ["date", "at", "review_date", "updated", "created"],
    "platform_id": ["platform_id", "reviewid", "review_id", "id"],
}


def _cutoff(config: dict) -> datetime:
    """Window start, computed once per run (conventions.md section 3.2)."""
    weeks = config["window_weeks"]
    return datetime.now(timezone.utc) - timedelta(weeks=weeks)


def fetch_play_store(config: dict, cutoff: datetime) -> pd.DataFrame:
    """Fetch public Play Store reviews, newest first, stop at window edge."""
    from google_play_scraper import Sort, reviews

    app_id = config["app"]["play_store_id"]
    rows: list[dict] = []
    token = None
    log.info("import: fetching Play Store reviews for %s", app_id)

    while True:
        batch, token = reviews(
            app_id,
            lang="en",
            country=config["app"]["country"],
            sort=Sort.NEWEST,
            count=200,
            continuation_token=token,
        )
        if not batch:
            break
        for r in batch:
            at = r["at"]
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            rows.append(
                {
                    "platform_id": r["reviewId"],
                    "store": "play",
                    "rating": r["score"],
                    "title": "",
                    "text": r["content"] or "",
                    "date": at,
                }
            )
        oldest = min(r["date"] for r in rows[-len(batch) :])
        log.info(
            "import: play store fetched %d rows (oldest %s)", len(rows), oldest.date()
        )
        if oldest < cutoff or token is None or len(rows) >= MAX_PLAY_REVIEWS:
            break

    log.info("import: play store returned %d rows (pre-filter)", len(rows))
    return pd.DataFrame(rows)


def fetch_app_store(config: dict, cutoff: datetime) -> pd.DataFrame:
    """Fetch public App Store reviews via the iTunes RSS JSON feed."""
    app_id = config["app"]["app_store_id"]
    country = config["app"]["country"]
    rows: list[dict] = []
    log.info("import: fetching App Store RSS for id %s (%s)", app_id, country)

    for page in range(1, RSS_MAX_PAGES + 1):
        url = (
            f"https://itunes.apple.com/{country}/rss/customerreviews/"
            f"page={page}/id={app_id}/sortby=mostrecent/json"
        )
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            entries = resp.json().get("feed", {}).get("entry", [])
        except (requests.RequestException, ValueError) as exc:
            log.warning("import: app store RSS page %d failed: %s", page, exc)
            break
        if isinstance(entries, dict):
            entries = [entries]
        page_rows = 0
        for e in entries:
            if "im:rating" not in e:  # first entry is app metadata (EC-IMP-03)
                continue
            rows.append(
                {
                    "platform_id": e["id"]["label"],
                    "store": "appstore",
                    "rating": int(e["im:rating"]["label"]),
                    "title": e.get("title", {}).get("label", ""),
                    "text": e.get("content", {}).get("label", ""),
                    "date": pd.to_datetime(e["updated"]["label"], utc=True),
                }
            )
            page_rows += 1
        if page_rows == 0:  # EC-IMP-02: stop on first empty page
            break

    log.info("import: app store returned %d rows (pre-filter)", len(rows))
    return pd.DataFrame(rows)


def load_manual_csvs() -> pd.DataFrame:
    """Best-effort load of any public exports dropped into data/raw/."""
    frames = []
    for path in sorted(RAW_DIR.glob("*.csv")):
        try:
            raw = pd.read_csv(path)
        except Exception as exc:
            log.error("import: skipping %s (unreadable: %s)", path.name, exc)
            continue
        lower = {c.lower().strip(): c for c in raw.columns}
        mapped: dict[str, str] = {}
        for canon, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in lower:
                    mapped[canon] = lower[alias]
                    break
        if "text" not in mapped or "rating" not in mapped:
            log.error(
                "import: skipping %s — cannot map text/rating (found: %s)",
                path.name,
                list(raw.columns),
            )
            continue
        if "date" not in mapped:  # EC-IMP-11
            log.error("import: skipping %s — no date column", path.name)
            continue
        df = pd.DataFrame({canon: raw[src] for canon, src in mapped.items()})
        if "platform_id" not in df.columns:
            df["platform_id"] = df.index.map(lambda i: f"{path.name}:{i}")
        df["store"] = "play" if "play" in path.name.lower() else "appstore"
        df["title"] = df.get("title", "")
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        frames.append(df)
        log.info("import: loaded %d rows from %s", len(df), path.name)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _normalize(df: pd.DataFrame, cutoff: datetime) -> pd.DataFrame:
    """Scrub, validate, window-filter, and coerce one source frame."""
    if df.empty:
        return df

    # PII boundary — before anything else touches the data further
    df = pii_scrub.scrub_frame(df, id_column="platform_id")

    # Rating sanity (EC-IMP-09)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    bad = df["rating"].isna() | ~df["rating"].between(1, 5)
    if bad.any():
        log.warning("import: dropping %d rows with invalid rating", int(bad.sum()))
        df = df[~bad]
    df["rating"] = df["rating"].astype(int)

    # Date sanity: unparseable / future-dated dropped (EC-IMP-12/13)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    now = datetime.now(timezone.utc)
    bad = df["date"].isna() | (df["date"] > now)
    if bad.any():
        log.warning("import: dropping %d rows with bad dates", int(bad.sum()))
        df = df[~bad]

    # Window filter, inclusive boundary (EC-IMP-04)
    df = df[df["date"] >= cutoff]

    # Empty text dropped (EC-IMP-01); long text truncated (EC-IMP-18)
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    empty = df["text"] == ""
    if empty.any():
        log.warning("import: dropping %d rows with empty text", int(empty.sum()))
        df = df[~empty]
    long_mask = df["text"].str.len() > MAX_TEXT_CHARS
    if long_mask.any():
        df.loc[long_mask, "text"] = (
            df.loc[long_mask, "text"].str.slice(0, MAX_TEXT_CHARS) + "…"
        )

    df["title"] = df["title"].fillna("").astype(str)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df[CANONICAL_COLUMNS]


def run(config: dict) -> Path:
    """Execute this stage. Writes data/reviews.csv atomically."""
    cutoff = _cutoff(config)
    log.info(
        "import: window cutoff %s (%d weeks)", cutoff.date(), config["window_weeks"]
    )

    sources = []
    try:
        sources.append(fetch_play_store(config, cutoff))
    except Exception as exc:  # EC-IMP-14/15: one source failing is survivable
        log.warning("import: play store fetch failed: %s", exc)
    try:
        sources.append(fetch_app_store(config, cutoff))
    except Exception as exc:
        log.warning("import: app store fetch failed: %s", exc)
    sources.append(load_manual_csvs())

    frames = [_normalize(df, cutoff) for df in sources if not df.empty]
    if not frames:
        raise PipelineError("import: 0 reviews in window from all sources")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["store", "review_id"])  # EC-IMP-08
    merged = merged.sort_values("date", ascending=False).reset_index(drop=True)

    if merged.empty:  # EC-IMP-05
        raise PipelineError("import: 0 reviews in window after filtering")
    if len(merged) < 20:  # EC-IMP-06
        log.warning("import: low volume week (%d reviews)", len(merged))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_CSV.with_suffix(".csv.tmp")
    merged.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(OUTPUT_CSV)

    by_store = merged["store"].value_counts().to_dict()
    log.info("import: wrote %d reviews %s -> %s", len(merged), by_store, OUTPUT_CSV)
    return OUTPUT_CSV
