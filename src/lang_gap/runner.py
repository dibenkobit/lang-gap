"""Orchestrator: load questions → call models → evaluate → save results."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml
from rich.console import Console
from rich.progress import Progress, TaskID

from lang_gap.client import CompletionResponse, OpenRouterClient
from lang_gap.config import MODELS
from lang_gap.evaluator import evaluate_coding, evaluate_reasoning
from lang_gap.extractor import extract_answer, extract_code
from lang_gap.schemas import (
    CodingQuestion,
    EvalResult,
    Question,
    ReasoningQuestion,
    RunResults,
)

console = Console()

QUESTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "questions"
RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"


# ── Question loading ─────────────────────────────────────────────────

def load_questions(categories: list[str] | None = None) -> list[Question]:
    """Load questions from YAML files in the questions/ directory."""
    questions: list[Question] = []

    for path in sorted(QUESTIONS_DIR.glob("*.yaml")):
        category = path.stem  # "coding" or "reasoning"
        if categories and category not in categories:
            continue

        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw:
            continue

        for item in raw:
            if item.get("category") == "coding":
                questions.append(CodingQuestion(**item))
            elif item.get("category") == "reasoning":
                questions.append(ReasoningQuestion(**item))

    return questions


# ── Prompt building ──────────────────────────────────────────────────

def build_prompt(question: Question, language: str) -> str:
    """Build the prompt sent to the model."""
    prompt_text = question.prompt_en if language == "en" else question.prompt_ru

    if isinstance(question, CodingQuestion):
        return (
            f"{prompt_text.strip()}\n\n"
            f"Write a Python function with the following signature:\n"
            f"{question.function_signature}\n\n"
            f"Return ONLY the function implementation inside a ```python code block. "
            f"Do not include examples, tests, or explanations."
        )

    return (
        f"{prompt_text.strip()}\n\n"
        f"Think step by step. End your response with exactly:\n"
        f"ANSWER: <your final answer>"
    )


# ── Single evaluation ────────────────────────────────────────────────

async def evaluate_single(
    client: OpenRouterClient,
    model_name: str,
    model_id: str,
    question: Question,
    language: str,
) -> EvalResult:
    """Send one prompt to one model, extract and evaluate the response."""
    prompt = build_prompt(question, language)

    try:
        resp: CompletionResponse = await client.complete(model_id, prompt)
    except Exception as exc:
        return EvalResult(
            question_id=question.id,
            model=model_name,
            language=language,
            raw_response="",
            extracted_answer=None,
            correct=False,
            error=f"API error: {exc}",
            latency_ms=0,
            tokens_used=0,
        )

    # Extract and evaluate
    extracted: str | None = None
    correct = False
    error: str | None = None

    if isinstance(question, CodingQuestion):
        code = extract_code(resp.content, question.function_name)
        if code is None:
            error = "Could not extract code from response"
        else:
            extracted = code
            correct, error = evaluate_coding(code, question)
    else:
        extracted = extract_answer(resp.content)
        if extracted is None:
            error = "Could not extract answer from response"
        else:
            correct = evaluate_reasoning(
                extracted, question.expected_answer, question.tolerance
            )

    return EvalResult(
        question_id=question.id,
        model=model_name,
        language=language,
        raw_response=resp.content,
        extracted_answer=extracted,
        correct=correct,
        error=error,
        latency_ms=resp.latency_ms,
        tokens_used=resp.tokens_used,
    )


# ── Main run ─────────────────────────────────────────────────────────

async def run(
    model_names: list[str] | None = None,
    categories: list[str] | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> RunResults | None:
    """Execute a full benchmark run."""
    questions = load_questions(categories)
    if limit is not None:
        questions = questions[:limit]

    if not questions:
        console.print("[red]No questions found. Check the questions/ directory.[/red]")
        return None

    selected_models = {
        name: mid
        for name, mid in MODELS.items()
        if model_names is None or name in model_names
    }

    if not selected_models:
        console.print("[red]No matching models found.[/red]")
        return None

    total_calls = len(selected_models) * 2 * len(questions)  # 2 languages
    console.print(
        f"[bold]Questions:[/bold] {len(questions)}  "
        f"[bold]Models:[/bold] {len(selected_models)}  "
        f"[bold]Total API calls:[/bold] {total_calls}"
    )

    if dry_run:
        console.print("\n[yellow]Dry run — no API calls will be made.[/yellow]")
        for name in selected_models:
            console.print(f"  • {name}")
        for q in questions:
            console.print(f"  • {q.id} ({q.category}, {q.difficulty})")
        return None

    results: list[EvalResult] = []

    async with OpenRouterClient() as client:
        with Progress(console=console) as progress:
            task: TaskID = progress.add_task("Evaluating...", total=total_calls)

            tasks: list[asyncio.Task[EvalResult]] = []
            for model_name, model_id in selected_models.items():
                for lang in ("en", "ru"):
                    for question in questions:
                        coro = evaluate_single(
                            client, model_name, model_id, question, lang
                        )
                        tasks.append(asyncio.create_task(coro))

            for coro_task in asyncio.as_completed(tasks):
                result = await coro_task
                results.append(result)
                progress.advance(task)

    run_id = uuid4().hex[:12]
    run_results = RunResults(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        models=list(selected_models.keys()),
        results=results,
    )

    # Save raw results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{run_id}.json"
    out_path.write_text(run_results.model_dump_json(indent=2))
    console.print(f"\n[green]Results saved to {out_path}[/green]")

    return run_results
