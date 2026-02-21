"""Generate comparison tables for terminal and markdown output."""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.text import Text

from lang_gap._paths import REPORTS_DIR
from lang_gap.schemas import EvalResult, RunResults

console = Console()

_PREFIX = {"coding": "code_", "reasoning": "reason_"}


@dataclass
class Score:
    correct: int
    total: int

    @property
    def pct(self) -> float:
        return self.correct / self.total if self.total else 0.0

    def display(self) -> str:
        if self.total == 0:
            return "—"
        return f"{self.pct * 100:.0f}% ({self.correct}/{self.total})"


def _score(
    results: list[EvalResult],
    predicate: Callable[[EvalResult], bool] | None = None,
) -> Score:
    filtered = [r for r in results if predicate is None or predicate(r)]
    correct = sum(1 for r in filtered if r.correct)
    return Score(correct=correct, total=len(filtered))


def _delta_cell(en: Score, ru: Score) -> Text:
    """Colored delta text for Rich table."""
    if en.total == 0 or ru.total == 0:
        return Text("—", style="dim")
    d = (ru.pct - en.pct) * 100
    if d == 0:
        return Text("0%", style="dim")
    sign = "+" if d > 0 else ""
    text = f"{sign}{d:.0f}%"
    style = "green" if d > 0 else "red" if d < -2 else "yellow"
    return Text(text, style=style)


def _delta_str(en: Score, ru: Score) -> str:
    if en.total == 0 or ru.total == 0:
        return "—"
    d = (ru.pct - en.pct) * 100
    sign = "+" if d > 0 else ""
    return f"{sign}{d:.0f}%"


def _make_predicate(
    lang: str, prefix: str | None = None
) -> Callable[[EvalResult], bool]:
    """Build a filter predicate for scoring."""
    if prefix is not None:
        return lambda r: r.language == lang and r.question_id.startswith(prefix)
    return lambda r: r.language == lang


def _model_scores(model_results: list[EvalResult]) -> dict[tuple[str, str], Score]:
    """Compute all scores for a single model."""
    s: dict[tuple[str, str], Score] = {}
    for cat in ("coding", "reasoning"):
        prefix = _PREFIX[cat]
        for lang in ("en", "ru"):
            s[(cat, lang)] = _score(model_results, _make_predicate(lang, prefix))
    for lang in ("en", "ru"):
        s[("all", lang)] = _score(model_results, _make_predicate(lang))
    return s


def print_report(run: RunResults) -> None:
    """Print rich tables to terminal and save markdown report."""
    results = run.results

    by_model: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_model[r.model].append(r)

    # Count unique questions per category across all models
    all_qids = {r.question_id for r in results}
    n_coding = sum(1 for q in all_qids if q.startswith("code_"))
    n_reasoning = sum(1 for q in all_qids if q.startswith("reason_"))

    # ── Header ──
    console.print()
    console.print(
        f"[bold]LangBench[/bold]  ·  {len(run.models)} models  ·  "
        f"{n_coding} coding + {n_reasoning} reasoning = {n_coding + n_reasoning} questions"
    )
    console.print()

    # Show category subtotals in column headers
    sections = []
    if n_coding > 0:
        sections.append(("coding", f"Coding ({n_coding} Qs)"))
    if n_reasoning > 0:
        sections.append(("reasoning", f"Reasoning ({n_reasoning} Qs)"))
    sections.append(("all", f"Overall ({n_coding + n_reasoning} Qs)"))

    # Build one table per section, print them sequentially
    for cat_key, section_title in sections:
        sec_table = Table(
            title=section_title,
            show_lines=True,
            pad_edge=True,
            expand=False,
            title_style="bold",
        )
        sec_table.add_column("Model", style="bold", min_width=18)
        sec_table.add_column("EN", justify="right", min_width=12)
        sec_table.add_column("RU", justify="right", min_width=12)
        sec_table.add_column("Δ", justify="center", min_width=5)

        for model in run.models:
            s = _model_scores(by_model[model])
            en = s[(cat_key, "en")]
            ru = s[(cat_key, "ru")]
            sec_table.add_row(
                model,
                en.display(),
                ru.display(),
                _delta_cell(en, ru),
            )

        console.print(sec_table)
        console.print()

    # ── EN-pass / RU-fail analysis ──
    lookup: dict[tuple[str, str], dict[str, bool]] = defaultdict(dict)
    for r in results:
        lookup[(r.question_id, r.model)][r.language] = r.correct

    en_pass_ru_fail = [
        (model, qid)
        for (qid, model), langs in lookup.items()
        if langs.get("en") and not langs.get("ru")
    ]

    if en_pass_ru_fail:
        console.print("[bold]Language gap — EN passed, RU failed:[/bold]")
        gap_table = Table(show_lines=False, pad_edge=True)
        gap_table.add_column("Model", style="bold")
        gap_table.add_column("Question")
        for model, qid in sorted(en_pass_ru_fail):
            gap_table.add_row(model, qid)
        console.print(gap_table)
        console.print()

    # ── Markdown report ──
    md = []
    md.append(f"# LangBench Report — {run.run_id}")
    md.append(f"_Generated: {run.timestamp}_\n")
    md.append(
        f"**{len(run.models)} models** · "
        f"**{n_coding}** coding + **{n_reasoning}** reasoning = "
        f"**{n_coding + n_reasoning}** questions\n"
    )

    for cat_key, section_title in sections:
        md.append(f"## {section_title}\n")
        md.append("| Model | EN | RU | Δ |")
        md.append("|-------|----|----|---|")
        for model in run.models:
            s = _model_scores(by_model[model])
            en = s[(cat_key, "en")]
            ru = s[(cat_key, "ru")]
            md.append(
                f"| {model} | {en.display()} | {ru.display()} | {_delta_str(en, ru)} |"
            )
        md.append("")

    if en_pass_ru_fail:
        md.append("## Language Gap — EN passed, RU failed\n")
        md.append("| Model | Question |")
        md.append("|-------|----------|")
        for model, qid in sorted(en_pass_ru_fail):
            md.append(f"| {model} | {qid} |")
        md.append("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / f"{run.run_id}.md"
    md_path.write_text("\n".join(md) + "\n")
    console.print(f"[green]Report saved to {md_path}[/green]")
