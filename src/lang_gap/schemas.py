"""Pydantic models for questions, evaluation results, and reports."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel


class TestCase(BaseModel):
    input: str  # Python expression, e.g. "func_name(1, 2)"
    expected: str  # Python literal, e.g. "3"


class CodingQuestion(BaseModel):
    id: str
    category: Literal["coding"]
    difficulty: Literal["easy", "medium", "hard"]
    prompt_en: str
    prompt_ru: str
    function_name: str
    function_signature: str  # e.g. "def is_palindrome(s: str) -> bool"
    test_cases: list[TestCase]


class ReasoningQuestion(BaseModel):
    id: str
    category: Literal["reasoning"]
    subcategory: Literal["math", "logic", "analytical"]
    difficulty: Literal["easy", "medium", "hard"]
    prompt_en: str
    prompt_ru: str
    expected_answer: str
    tolerance: float | None = None


Question = Union[CodingQuestion, ReasoningQuestion]


class EvalResult(BaseModel):
    question_id: str
    model: str
    language: Literal["en", "ru"]
    raw_response: str
    extracted_answer: str | None = None
    correct: bool
    error: str | None = None
    latency_ms: int
    tokens_used: int


class RunResults(BaseModel):
    run_id: str
    timestamp: str
    models: list[str]
    results: list[EvalResult]
