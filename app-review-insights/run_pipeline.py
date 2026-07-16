"""App Review Insights Analyser — single pipeline entry point.

Usage:
    python run_pipeline.py                  # full run, defaults from config.yaml
    python run_pipeline.py --weeks 10      # override window
    python run_pipeline.py --from group    # resume from a stage
    python run_pipeline.py --reuse-legend  # pin last week's themes
    python run_pipeline.py --dry-run       # walk stages without LLM calls / email

Exit codes: 0 success, 1 pipeline error, 2 config error.
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.errors import PipelineError

ROOT = Path(__file__).parent
STAGES = ["import", "group", "note", "email"]

log = logging.getLogger("pipeline")


def load_config(args: argparse.Namespace) -> dict:
    """Load config.yaml, apply CLI overrides, validate. Exit code 2 on failure."""
    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        print(f"config error: {config_path} not found", file=sys.stderr)
        sys.exit(2)

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # CLI overrides config; config overrides defaults (conventions.md section 6)
    if args.weeks is not None:
        config["window_weeks"] = args.weeks
    config["reuse_legend"] = args.reuse_legend
    config["dry_run"] = args.dry_run

    weeks = config.get("window_weeks")
    if not isinstance(weeks, int) or not 8 <= weeks <= 12:
        print(
            f"config error: window_weeks must be 8-12 (got {weeks!r})",
            file=sys.stderr,
        )
        sys.exit(2)

    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="App Review Insights pipeline")
    parser.add_argument(
        "--weeks", type=int, default=None, help="window in weeks (8-12)"
    )
    parser.add_argument(
        "--from",
        dest="from_stage",
        choices=STAGES,
        default="import",
        help="resume from this stage",
    )
    parser.add_argument(
        "--reuse-legend",
        action="store_true",
        help="reuse the pinned theme legend for consistent week-over-week trends",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="walk all stages without LLM calls or email drafting",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    load_dotenv(ROOT / ".env")

    args = parse_args()
    config = load_config(args)

    # Import stage modules lazily so a --dry-run works before deps are installed.
    from src import draft_email, generate_note, group_themes, import_reviews

    stage_runners = {
        "import": import_reviews.run,
        "group": group_themes.run,
        "note": generate_note.run,
        "email": draft_email.run,
    }

    start = STAGES.index(args.from_stage)
    to_run = STAGES[start:]
    log.info(
        "stages to run: %s (window: %s weeks)",
        " -> ".join(to_run),
        config["window_weeks"],
    )

    results: dict[str, Path] = {}
    for stage in to_run:
        if config["dry_run"]:
            log.info("[dry-run] stage %-6s — skipped", stage)
            continue
        log.info("stage %-6s — starting", stage)
        try:
            results[stage] = stage_runners[stage](config)
            log.info("stage %-6s — done -> %s", stage, results[stage])
        except PipelineError as exc:
            log.error("stage %-6s — failed: %s", stage, exc)
            return 1
        except NotImplementedError as exc:
            log.error("stage %-6s — %s", stage, exc)
            return 1

    if config["dry_run"]:
        print("Dry run complete.")
        return 0

    print("\n=== Weekly pulse pipeline complete ===")
    summary_json = ROOT / "output" / "theme_counts.json"
    if summary_json.exists():
        import json

        stats = json.loads(summary_json.read_text(encoding="utf-8"))
        print(
            f"Reviews analyzed : {stats['total_reviews']} (week ending {stats['week_ending']})"
        )
        themes = ", ".join(f"{t} ({c})" for t, c in stats["totals"].items())
        print(f"Themes           : {themes}")
    for stage, label in [("note", "Weekly note"), ("email", "Email draft")]:
        if stage in results:
            print(f"{label:<17}: {results[stage]}")
    print(
        "Re-run next week : python run_pipeline.py  (add --reuse-legend for stable trends)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
