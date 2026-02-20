"""Tests for code execution and answer comparison logic."""

from lang_gap.evaluator import _build_test_harness, evaluate_coding, evaluate_reasoning
from lang_gap.schemas import CodingQuestion, TestCase


class TestEvaluateReasoning:
    def test_exact_match(self):
        assert evaluate_reasoning("42", "42", None) is True

    def test_case_insensitive(self):
        assert evaluate_reasoning("Yes", "yes", None) is True

    def test_whitespace_stripped(self):
        assert evaluate_reasoning("  42  ", "42", None) is True

    def test_mismatch(self):
        assert evaluate_reasoning("41", "42", None) is False

    def test_numeric_tolerance(self):
        assert evaluate_reasoning("3.14", "3.14159", 0.01) is True

    def test_numeric_no_tolerance(self):
        assert evaluate_reasoning("3.14", "3.14159", None) is False

    def test_non_numeric_mismatch(self):
        assert evaluate_reasoning("cat", "dog", None) is False


class TestEvaluateCoding:
    def _make_question(
        self, function_name: str, signature: str, test_cases: list[TestCase]
    ) -> CodingQuestion:
        return CodingQuestion(
            id="test_001",
            category="coding",
            difficulty="easy",
            prompt_en="test",
            prompt_ru="test",
            function_name=function_name,
            function_signature=signature,
            test_cases=test_cases,
        )

    def test_correct_code_passes(self):
        code = "def add(a, b):\n    return a + b"
        question = self._make_question(
            "add",
            "def add(a: int, b: int) -> int",
            [TestCase(input="add(1, 2)", expected="3")],
        )
        passed, error = evaluate_coding(code, question)
        assert passed is True
        assert error is None

    def test_wrong_code_fails(self):
        code = "def add(a, b):\n    return a - b"
        question = self._make_question(
            "add",
            "def add(a: int, b: int) -> int",
            [TestCase(input="add(1, 2)", expected="3")],
        )
        passed, error = evaluate_coding(code, question)
        assert passed is False
        assert error is not None
        assert "FAIL" in error

    def test_syntax_error_fails(self):
        code = "def add(a, b)\n    return a + b"  # missing colon
        question = self._make_question(
            "add",
            "def add(a: int, b: int) -> int",
            [TestCase(input="add(1, 2)", expected="3")],
        )
        passed, error = evaluate_coding(code, question)
        assert passed is False
        assert "Runtime error" in (error or "")

    def test_infinite_loop_times_out(self):
        code = "def loop():\n    while True: pass"
        question = self._make_question(
            "loop",
            "def loop() -> None",
            [TestCase(input="loop()", expected="None")],
        )
        passed, error = evaluate_coding(code, question)
        assert passed is False
        assert "timed out" in (error or "").lower()

    def test_multiple_test_cases(self):
        code = "def double(x):\n    return x * 2"
        question = self._make_question(
            "double",
            "def double(x: int) -> int",
            [
                TestCase(input="double(3)", expected="6"),
                TestCase(input="double(0)", expected="0"),
                TestCase(input="double(-1)", expected="-2"),
            ],
        )
        passed, error = evaluate_coding(code, question)
        assert passed is True
        assert error is None


class TestBuildTestHarness:
    def test_harness_contains_code_and_tests(self):
        harness = _build_test_harness(
            "def f(): pass",
            "f",
            [TestCase(input="f()", expected="None")],
        )
        assert "def f(): pass" in harness
        assert "import math" in harness
        assert "PASS:" in harness
        assert "FAIL:" in harness
