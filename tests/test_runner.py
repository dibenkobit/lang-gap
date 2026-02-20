"""Tests for question loading and prompt building."""

from lang_gap.runner import build_prompt, load_questions
from lang_gap.schemas import CodingQuestion, ReasoningQuestion


class TestLoadQuestions:
    def test_loads_all_questions(self):
        questions = load_questions()
        assert len(questions) == 100

    def test_filter_coding_only(self):
        questions = load_questions(categories=["coding"])
        assert len(questions) == 50
        assert all(isinstance(q, CodingQuestion) for q in questions)

    def test_filter_reasoning_only(self):
        questions = load_questions(categories=["reasoning"])
        assert len(questions) == 50
        assert all(isinstance(q, ReasoningQuestion) for q in questions)

    def test_all_ids_unique(self):
        questions = load_questions()
        ids = [q.id for q in questions]
        assert len(ids) == len(set(ids))

    def test_all_have_both_prompts(self):
        for q in load_questions():
            assert q.prompt_en.strip(), f"{q.id} has empty prompt_en"
            assert q.prompt_ru.strip(), f"{q.id} has empty prompt_ru"


class TestBuildPrompt:
    def _coding_question(self) -> CodingQuestion:
        return CodingQuestion(
            id="test_001",
            category="coding",
            difficulty="easy",
            prompt_en="Count odd-length words.",
            prompt_ru="Подсчитайте слова с нечётной длиной.",
            function_name="count_odd",
            function_signature="def count_odd(s: str) -> int",
            test_cases=[],
        )

    def _reasoning_question(self) -> ReasoningQuestion:
        return ReasoningQuestion(
            id="test_002",
            category="reasoning",
            subcategory="math",
            difficulty="easy",
            prompt_en="What is 2+2?",
            prompt_ru="Сколько будет 2+2?",
            expected_answer="4",
        )

    def test_coding_en_includes_signature(self):
        prompt = build_prompt(self._coding_question(), "en")
        assert "def count_odd(s: str) -> int" in prompt
        assert "Count odd-length words." in prompt

    def test_coding_ru_uses_russian_prompt(self):
        prompt = build_prompt(self._coding_question(), "ru")
        assert "Подсчитайте" in prompt
        assert "Count odd-length words." not in prompt

    def test_coding_asks_for_code_block(self):
        prompt = build_prompt(self._coding_question(), "en")
        assert "```python" in prompt

    def test_reasoning_en_asks_for_answer_tag(self):
        prompt = build_prompt(self._reasoning_question(), "en")
        assert "ANSWER:" in prompt
        assert "What is 2+2?" in prompt

    def test_reasoning_ru_uses_russian_prompt(self):
        prompt = build_prompt(self._reasoning_question(), "ru")
        assert "Сколько будет 2+2?" in prompt
        assert "What is 2+2?" not in prompt
