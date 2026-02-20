"""CLI entry point: python -m lang_gap"""

from __future__ import annotations

import argparse
import asyncio
import sys

from lang_gap.config import MODELS
from lang_gap.report import print_report
from lang_gap.runner import run


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="lang-gap",
        description="EN vs RU LLM benchmark via OpenRouter",
    )
    p.add_argument(
        "--models",
        default="all",
        help=f"Comma-separated model names or 'all'. Available: {', '.join(MODELS)}",
    )
    p.add_argument(
        "--questions",
        default="all",
        help="Comma-separated categories (coding, reasoning) or 'all'",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max questions to evaluate (for quick test runs)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup and print what would run, without API calls",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    model_names: list[str] | None = None
    if args.models != "all":
        model_names = [m.strip() for m in args.models.split(",")]
        unknown = set(model_names) - set(MODELS)
        if unknown:
            print(f"Unknown models: {unknown}. Available: {list(MODELS)}")
            sys.exit(1)

    categories: list[str] | None = None
    if args.questions != "all":
        categories = [c.strip() for c in args.questions.split(",")]
        valid = {"coding", "reasoning"}
        unknown = set(categories) - valid
        if unknown:
            print(f"Unknown categories: {unknown}. Available: {valid}")
            sys.exit(1)

    results = asyncio.run(
        run(
            model_names=model_names,
            categories=categories,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )

    if results:
        print_report(results)


if __name__ == "__main__":
    main()
