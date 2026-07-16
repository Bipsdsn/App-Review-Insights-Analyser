"""Stage 3: Generate the <=250-word weekly pulse note.

Quote pool and stats are assembled in code; one LLM call writes the note;
deterministic gates validate it (word count -> compress retry -> truncate,
quote substring check -> re-select, PII re-scan). Failures are saved with
a .FAILED.md suffix for inspection.
"""

import json
import logging
import re
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd

from src import llm_client, pii_scrub
from src.errors import PipelineError

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
THEMED_CSV = ROOT / "data" / "reviews_themed.csv"
COUNTS_JSON = ROOT / "output" / "theme_counts.json"
ARCHIVE_DIR = ROOT / "output" / "archive"

MAX_WORDS = 250
QUOTE_MIN, QUOTE_MAX = 40, 200
POOL_SIZE = 15
SENTIMENT_THEME_HINTS = ("general", "sentiment", "praise")


def _is_sentiment_theme(name: str) -> bool:
    return any(h in name.lower() for h in SENTIMENT_THEME_HINTS)


def top_themes(stats: dict, n: int = 3) -> list[str]:
    """Top themes by volume, skipping the general-sentiment bucket so the
    note focuses on actionable topics. Tiebreak: lower avg rating first
    (EC-THM-13)."""
    ranked = sorted(
        stats["totals"].items(),
        key=lambda kv: (-kv[1], stats["avg_rating"].get(kv[0], 5)),
    )
    topical = [t for t, _ in ranked if not _is_sentiment_theme(t)]
    return topical[:n]


def build_quote_pool(df: pd.DataFrame, themes: list[str]) -> list[dict]:
    """Code-side candidate selection: vivid, clean, right-sized quotes."""
    pool: list[dict] = []
    for theme in themes:
        sub = df[df["theme"] == theme].copy()
        sub["len"] = sub["text"].str.len()
        sub = sub[
            sub["len"].between(QUOTE_MIN, QUOTE_MAX)
            & ~sub["text"].str.contains(re.escape(pii_scrub.REDACTED), na=False)
        ]
        # rating extremes read most vividly
        sub["extremity"] = (sub["rating"] - 3).abs()
        sub = sub.sort_values(["extremity", "len"], ascending=[False, False])
        for r in sub.head(POOL_SIZE // len(themes) + 2).itertuples():
            pool.append({"theme": theme, "text": r.text.strip()})
    return pool[:POOL_SIZE]


def wow_deltas(stats: dict) -> dict[str, str]:
    """Week-over-week % change per theme vs the newest previous archive."""
    current_file = f"theme_counts_{stats['week_ending']}.json"
    previous = sorted(
        p for p in ARCHIVE_DIR.glob("theme_counts_*.json") if p.name != current_file
    )
    if not previous:  # EC-NOTE-09
        return {}
    prev = json.loads(previous[-1].read_text(encoding="utf-8"))
    deltas = {}
    for theme, count in stats["totals"].items():
        old = prev.get("totals", {}).get(theme)
        if old is None or old == 0:  # EC-NOTE-08
            deltas[theme] = "new"
        else:
            pct = (count - old) / old * 100
            deltas[theme] = f"{pct:+.0f}% WoW"
    return deltas


def _normalize_for_match(s: str) -> str:
    """Whitespace + unicode-quote normalization for substring checks
    (EC-NOTE-03)."""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def count_words(note: str) -> int:
    """Word count on rendered-ish text: markdown tokens stripped
    (EC-NOTE-11)."""
    text = re.sub(r"[#*_|>`\[\]]", " ", note)
    return len(text.split())


def extract_quotes(note: str) -> list[str]:
    """Pull quoted strings (>= 4 words) out of the note for verification."""
    candidates = re.findall(r'[""]([^""]+)[""]|"([^"]+)"', note)
    quotes = [a or b for a, b in candidates]
    return [q for q in quotes if len(q.split()) >= 4]


def verify_quotes(note: str, source_texts: pd.Series) -> list[str]:
    """Every quote must be a substring of some source review (EC-NOTE-02)."""
    haystack = " ||| ".join(source_texts.fillna("").map(_normalize_for_match))
    return [q for q in extract_quotes(note) if _normalize_for_match(q) not in haystack]


def _fallback_insert_quotes(note: str, pool: list[dict]) -> str:
    """Final fallback: replace the quotes section with verbatim pool quotes."""
    lines = [f'- *"{q["text"]}"* — [{q["theme"]}]' for q in pool[:3]]
    section = "## What Users Are Saying\n" + "\n".join(lines)
    return re.sub(
        r"## What Users Are Saying.*?(?=## |\Z)", section + "\n\n", note, flags=re.S
    )


def run(config: dict) -> Path:
    """Execute this stage. Reads themed data, writes the validated note."""
    if not THEMED_CSV.exists() or not COUNTS_JSON.exists():
        raise PipelineError("note: themed data missing — run the group stage first")
    df = pd.read_csv(THEMED_CSV)
    stats = json.loads(COUNTS_JSON.read_text(encoding="utf-8"))

    themes = top_themes(stats)
    if not themes:
        raise PipelineError("note: no topical themes found")
    log.info("note: top themes %s", themes)

    pool = build_quote_pool(df, themes)
    if len(pool) < 3:  # EC-NOTE-05: relax filter
        log.warning("note: thin quote pool (%d), relaxing length filter", len(pool))
        global QUOTE_MIN, QUOTE_MAX
        QUOTE_MIN, QUOTE_MAX = 20, 300
        pool = build_quote_pool(df, themes)

    deltas = wow_deltas(stats)
    stats_lines = []
    for t in themes:
        line = (
            f"- {t}: {stats['totals'][t]} reviews, avg {stats['avg_rating'][t]} stars"
            + (f", {deltas[t]}" if t in deltas else "")
        )
        stats_lines.append(line)
    sentiment = [t for t in stats["totals"] if _is_sentiment_theme(t)]
    for t in sentiment:
        stats_lines.append(
            f"- (context) {t}: {stats['totals'][t]} reviews, avg {stats['avg_rating'][t]} stars"
        )

    prompt_template = (ROOT / "prompts" / "weekly_note.txt").read_text(encoding="utf-8")
    prompt = prompt_template.format(
        week_ending=stats["week_ending"],
        total_reviews=stats["total_reviews"],
        window_weeks=config["window_weeks"],
        wow_hint=", WoW change if given" if deltas else "",
        stats="\n".join(stats_lines),
        quote_pool="\n".join(f'[{q["theme"]}] "{q["text"]}"' for q in pool),
    )

    note = llm_client.complete(prompt, config, json_mode=False, temperature=0.3)

    # Gate 0: strip any preamble before the first heading (EC-NOTE-10)
    if "#" in note:
        note = note[note.index("#") :]

    # Gate 1: word count -> one compress retry -> hard truncate (EC-NOTE-01)
    if count_words(note) > MAX_WORDS:
        log.warning("note: %d words > %d, compress retry", count_words(note), MAX_WORDS)
        note = llm_client.complete(
            f"Compress this note to under {MAX_WORDS} words. Keep the exact structure, "
            f"all numbers, and all quotes word-for-word:\n\n{note}",
            config,
            json_mode=False,
            temperature=0.0,
        )
        if "#" in note:
            note = note[note.index("#") :]
        while count_words(note) > MAX_WORDS:
            note = "\n".join(note.splitlines()[:-1])  # trim from the end

    # Gate 2: quote verification -> fallback to code-inserted quotes
    bad = verify_quotes(note, df["text"])
    if bad:
        log.warning(
            "note: %d unverified quotes, inserting pool quotes verbatim", len(bad)
        )
        note = _fallback_insert_quotes(note, pool)
        still_bad = verify_quotes(note, df["text"])
        if still_bad:
            failed = (
                ROOT / "output" / f"weekly_note_{date.today().isoformat()}.FAILED.md"
            )
            failed.write_text(note, encoding="utf-8")
            raise PipelineError(
                f"note: quotes failed verification even after fallback -> {failed}"
            )

    # Gate 3: PII re-scan (defense in depth)
    if pii_scrub.contains_pii(note):
        note = pii_scrub.scrub_text(note)
        log.warning("note: PII pattern redacted in final note")

    out = ROOT / "output" / f"weekly_note_{date.today().isoformat()}.md"
    tmp = out.with_suffix(".md.tmp")
    tmp.write_text(note, encoding="utf-8")
    tmp.replace(out)
    log.info(
        "note: %d words, %d quotes verified -> %s",
        count_words(note),
        len(extract_quotes(note)),
        out,
    )
    return out
