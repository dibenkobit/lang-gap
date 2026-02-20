"""Tests for LLM response extraction logic."""

from lang_gap.extractor import extract_answer, extract_code


class TestExtractCode:
    def test_fenced_python_block(self):
        response = "Here's the solution:\n```python\ndef add(a, b):\n    return a + b\n```"
        assert extract_code(response, "add") == "def add(a, b):\n    return a + b"

    def test_prefers_block_with_target_function(self):
        response = (
            "```python\nimport math\n```\n"
            "```python\ndef solve(x):\n    return x * 2\n```"
        )
        assert extract_code(response, "solve") == "def solve(x):\n    return x * 2"

    def test_falls_back_to_first_block(self):
        response = "```python\nresult = 42\n```"
        assert extract_code(response, "nonexistent") == "result = 42"

    def test_bare_function_without_fence(self):
        response = "Sure, here you go:\ndef greet(name):\n    return f'Hello {name}'\n\nDone."
        result = extract_code(response, "greet")
        assert result is not None
        assert "def greet(name):" in result

    def test_returns_none_when_no_code(self):
        response = "I cannot solve this problem."
        assert extract_code(response, "solve") is None

    def test_py_language_tag(self):
        response = "```py\ndef foo():\n    pass\n```"
        assert extract_code(response, "foo") == "def foo():\n    pass"


class TestExtractAnswer:
    def test_answer_tag(self):
        response = "Let me think...\nANSWER: 42"
        assert extract_answer(response) == "42"

    def test_case_insensitive(self):
        response = "answer: hello world"
        assert extract_answer(response) == "hello world"

    def test_last_occurrence_wins(self):
        response = "ANSWER: wrong\nWait, let me reconsider.\nANSWER: correct"
        assert extract_answer(response) == "correct"

    def test_fallback_to_last_number(self):
        response = "The answer is clearly 7 because 3 + 4 = 7"
        assert extract_answer(response) == "7"

    def test_fallback_negative_number(self):
        response = "The result is -15"
        assert extract_answer(response) == "-15"

    def test_fallback_float(self):
        response = "So the final value is 3.14"
        assert extract_answer(response) == "3.14"

    def test_returns_none_when_no_answer(self):
        response = "I have no idea."
        assert extract_answer(response) is None
