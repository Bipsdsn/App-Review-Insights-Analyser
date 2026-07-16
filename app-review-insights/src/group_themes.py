"""Stage 2: Group reviews into <=5 themes via two-pass LLM classification.

Pass 1 discovers the theme legend from a sample (or loads the pinned legend
with --reuse-legend); Pass 2 classifies all reviews in batches of 25 at
temperature 0.0. Writes data/reviews_themed.csv, output/theme_legend.md,
and output/theme_counts.json (+ dated archive copy).
"""

import json
import logging
from datetime import date
from pathlib import Path

import pandas as pd

from src import llm_client
from src.errors import PipelineError

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "data" / "reviews.csv"
OUTPUT_CSV = ROOT / "data" / "reviews_themed.csv"
LEGEND_MD = ROOT / "output" / "theme_legend.md"
LEGEND_JSON = ROOT / "output" / "theme_legend.json"
COUNTS_JSON = ROOT / "output" / "theme_counts.json"
ARCHIVE_DIR = ROOT / "output" / "archive"

DISCOVERY_SAMPLE = 100
DISCOVERY_TRUNC = 200  # chars per review in the discovery sample
OTHER = "Other"
OTHER_WARN_RATIO = 0.15  # EC-THM-05


def _load_prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def _dedupe_themes(themes: list[dict]) -> list[dict]:
    """Case-insensitive dedupe, preserve order (EC-THM-03)."""
    seen: set[str] = set()
    out = []
    for t in themes:
        key = t["name"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(
                {
                    "name": t["name"].strip(),
                    "definition": t.get("definition", "").strip(),
                }
            )
    return out


def discover_legend(df: pd.DataFrame, config: dict) -> list[dict]:
    """Pass 1: one LLM call proposes <= max_themes topic-based themes."""
    sample = df.sample(n=min(DISCOVERY_SAMPLE, len(df)), random_state=42)
    lines = [f"{r.rating} | {r.text[:DISCOVERY_TRUNC]}" for r in sample.itertuples()]
    prompt = _load_prompt("theme_discovery.txt").format(
        max_themes=config["max_themes"],
        reviews_sample="\n".join(lines),
    )
    result = llm_client.complete_json(prompt, config, temperature=0.2)
    themes = _dedupe_themes(result.get("themes", []))
    if not themes:
        raise PipelineError("group: discovery returned no themes")
    if len(themes) > config["max_themes"]:  # EC-THM-01
        log.warning(
            "group: LLM proposed %d themes, truncating to %d",
            len(themes),
            config["max_themes"],
        )
        themes = themes[: config["max_themes"]]
    return themes


def load_pinned_legend() -> list[dict]:
    if not LEGEND_JSON.exists():
        raise PipelineError(
            "group: --reuse-legend set but no pinned legend found; run once without it"
        )
    return json.loads(LEGEND_JSON.read_text(encoding="utf-8"))


def write_legend(themes: list[dict]) -> None:
    LEGEND_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Theme Legend", ""]
    lines += [f"- **{t['name']}** — {t['definition']}" for t in themes]
    tmp = LEGEND_MD.with_suffix(".md.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(LEGEND_MD)
    LEGEND_JSON.write_text(json.dumps(themes, indent=2), encoding="utf-8")


def classify(df: pd.DataFrame, themes: list[dict], config: dict) -> dict[str, str]:
    """Pass 2: batched classification at temperature 0.0."""
    legend_text = "\n".join(f"- {t['name']}: {t['definition']}" for t in themes)
    valid = {t["name"] for t in themes}
    template = _load_prompt("classify_batch.txt")

    labels: dict[str, str] = {}
    pending = list(df.itertuples())
    batch_size = llm_client.BATCH_SIZE
    n_batches = (len(pending) + batch_size - 1) // batch_size

    for attempt in range(2):  # second pass re-queues missing ids (EC-THM-07)
        next_pending = []
        for i in range(0, len(pending), batch_size):
            batch = pending[i : i + batch_size]
            lines = [f"{r.review_id} | {r.rating} | {r.text[:300]}" for r in batch]
            prompt = template.format(legend=legend_text, reviews_batch="\n".join(lines))
            result = llm_client.complete_json(
                prompt, config, temperature=0.0, fast=True
            )

            batch_ids = {r.review_id for r in batch}
            for rid, theme in result.items():
                if rid not in batch_ids:  # hallucinated key (EC-THM-08)
                    log.warning("group: ignoring unknown review_id %s in response", rid)
                    continue
                labels[rid] = theme if theme in valid else None
            for r in batch:
                if labels.get(r.review_id) is None:
                    labels.pop(r.review_id, None)
                    next_pending.append(r)
            done = min(i + batch_size, len(pending))
            log.info(
                "group: classified %d/%d (pass %d)", done, len(pending), attempt + 1
            )
        pending = next_pending
        if not pending:
            break

    for r in pending:  # EC-THM-04/07 final fallback
        labels[r.review_id] = OTHER
    if pending:
        log.warning("group: %d reviews fell back to '%s'", len(pending), OTHER)
    log.info(
        "group: classification done (%d reviews, ~%d calls)", len(labels), n_batches
    )
    return labels


def aggregate(df: pd.DataFrame) -> dict:
    counts = df.groupby("theme").agg(
        count=("theme", "size"), avg_rating=("rating", "mean")
    )
    counts = counts.sort_values("count", ascending=False)
    return {
        "week_ending": date.today().isoformat(),
        "total_reviews": int(len(df)),
        "totals": {t: int(c) for t, c in counts["count"].items()},
        "avg_rating": {t: round(float(r), 2) for t, r in counts["avg_rating"].items()},
    }


def run(config: dict) -> Path:
    """Execute this stage. Reads data/reviews.csv, writes themed outputs."""
    if not INPUT_CSV.exists():
        raise PipelineError(
            "group: data/reviews.csv missing — run the import stage first"
        )
    df = pd.read_csv(INPUT_CSV)
    log.info("group: loaded %d reviews", len(df))

    if config.get("reuse_legend"):
        themes = load_pinned_legend()
        log.info("group: reusing pinned legend (%d themes)", len(themes))
    else:
        themes = discover_legend(df, config)
        log.info("group: discovered legend: %s", [t["name"] for t in themes])
    write_legend(themes)

    labels = classify(df, themes, config)
    df["theme"] = df["review_id"].map(labels)

    other_ratio = (df["theme"] == OTHER).mean()
    if other_ratio > OTHER_WARN_RATIO:  # EC-THM-05
        log.warning(
            "group: '%s' bucket is %.0f%% — legend may miss a real theme; "
            "consider re-running discovery",
            OTHER,
            other_ratio * 100,
        )

    tmp = OUTPUT_CSV.with_suffix(".csv.tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(OUTPUT_CSV)

    stats = aggregate(df)
    COUNTS_JSON.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive = ARCHIVE_DIR / f"theme_counts_{stats['week_ending']}.json"
    archive.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    log.info("group: theme counts %s -> %s", stats["totals"], OUTPUT_CSV)
    return OUTPUT_CSV
