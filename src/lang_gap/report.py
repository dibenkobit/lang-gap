"""Generate comparison tables for terminal and markdown output."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

from lang_gap.schemas import RunResults

console = Console()
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def _accuracy(results: list, predicate=None) -> float:
    """Compute accuracy (0.0–1.0) for results matching predicate."""
    filtered = [r for r in results if predicate is None or predicate(r)]
    if not filtered:
        return 0.0
    return sum(1 for r in filtered if r.correct) / len(filtered)


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def _delta(en: float, ru: float) -> str:
    d = (ru - en) * 100
    sign = "+" if d > 0 else ""
    return f"{sign}{d:.0f}%"


def print_report(run: RunResults) -> None:
    """Print a rich table to the terminal and save markdown report."""
    results = run.results

    # Group by model
    by_model: dict[str, list] = defaultdict(list)
    for r in results:
        by_model[r.model].append(r)

    # ── Main comparison table ──
    table = Table(title="LangBench Results", show_lines=True)
    table.add_column("Model", style="bold")
    table.add_column("EN (coding)")
    table.add_column("RU (coding)")
    table.add_column("Δ coding", style="dim")
    table.add_column("EN (reason)")
    table.add_column("RU (reason)")
    table.add_column("Δ reason", style="dim")
    table.add_column("EN (all)")
    table.add_column("RU (all)")
    table.add_column("Δ all", style="bold")

    md_lines: list[str] = [
        f"# LangBench Report — {run.run_id}",
        f"_Generated: {run.timestamp}_\n",
        "## Overall Results\n",
        "| Model | EN (coding) | RU (coding) | Δ | EN (reason) | RU (reason) | Δ | EN (all) | RU (all) | Δ |",
        "|-------|------------|------------|---|------------|------------|---|---------|---------|---|",
    ]

    for model in run.models:
        mr = by_model[model]

        _PREFIX = {"coding": "code_", "reasoning": "reason_"}

        def _cat(cat: str, lang: str):
            prefix = _PREFIX[cat]
            return _accuracy(
                mr,
                lambda r, p=prefix, la=lang: r.language == la
                and r.question_id.startswith(p),
            )

        en_code = _cat("coding", "en")
        ru_code = _cat("coding", "ru")
        en_reas = _cat("reasoning", "en")
        ru_reas = _cat("reasoning", "ru")
        en_all = _accuracy(mr, lambda r: r.language == "en")
        ru_all = _accuracy(mr, lambda r: r.language == "ru")

        table.add_row(
            model,
            _pct(en_code), _pct(ru_code), _delta(en_code, ru_code),
            _pct(en_reas), _pct(ru_reas), _delta(en_reas, ru_reas),
            _pct(en_all), _pct(ru_all), _delta(en_all, ru_all),
        )

        md_lines.append(
            f"| {model} | {_pct(en_code)} | {_pct(ru_code)} | {_delta(en_code, ru_code)} "
            f"| {_pct(en_reas)} | {_pct(ru_reas)} | {_delta(en_reas, ru_reas)} "
            f"| {_pct(en_all)} | {_pct(ru_all)} | {_delta(en_all, ru_all)} |"
        )

    console.print(table)

    # ── EN-pass / RU-fail analysis ──
    en_pass_ru_fail: list[tuple[str, str, str]] = []
    # Build lookup: (question_id, model) → {lang: correct}
    lookup: dict[tuple[str, str], dict[str, bool]] = defaultdict(dict)
    for r in results:
        lookup[(r.question_id, r.model)][r.language] = r.correct

    for (qid, model), langs in lookup.items():
        if langs.get("en") and not langs.get("ru"):
            en_pass_ru_fail.append((model, qid, "EN ✓ / RU ✗"))

    if en_pass_ru_fail:
        console.print("\n[bold]Questions where EN passed but RU failed:[/bold]")
        gap_table = Table(show_lines=False)
        gap_table.add_column("Model")
        gap_table.add_column("Question")
        gap_table.add_column("Status")
        for model, qid, status in sorted(en_pass_ru_fail):
            gap_table.add_row(model, qid, status)
        console.print(gap_table)

        md_lines.append("\n## Language Gap — EN pass / RU fail\n")
        md_lines.append("| Model | Question | Status |")
        md_lines.append("|-------|----------|--------|")
        for model, qid, status in sorted(en_pass_ru_fail):
            md_lines.append(f"| {model} | {qid} | {status} |")

    # Save markdown
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / f"{run.run_id}.md"
    md_path.write_text("\n".join(md_lines) + "\n")
    console.print(f"\n[green]Markdown report saved to {md_path}[/green]")
