"""Tests for scoring logic."""

from lang_gap.report import Score, _score


class TestScore:
    def test_percentage(self):
        s = Score(correct=3, total=4)
        assert s.pct == 0.75

    def test_percentage_zero_total(self):
        s = Score(correct=0, total=0)
        assert s.pct == 0.0

    def test_display(self):
        s = Score(correct=8, total=10)
        assert s.display() == "80% (8/10)"

    def test_display_zero(self):
        s = Score(correct=0, total=0)
        assert s.display() == "\u2014"  # em dash

    def test_display_perfect(self):
        s = Score(correct=5, total=5)
        assert s.display() == "100% (5/5)"


class TestScoreFunction:
    def test_unfiltered(self):
        # Minimal objects that have a .correct attribute
        class FakeResult:
            def __init__(self, correct: bool):
                self.correct = correct

        results = [FakeResult(True), FakeResult(True), FakeResult(False)]
        s = _score(results)
        assert s.correct == 2
        assert s.total == 3

    def test_with_predicate(self):
        class FakeResult:
            def __init__(self, correct: bool, lang: str):
                self.correct = correct
                self.lang = lang

        results = [
            FakeResult(True, "en"),
            FakeResult(False, "ru"),
            FakeResult(True, "en"),
        ]
        s = _score(results, predicate=lambda r: r.lang == "en")
        assert s.correct == 2
        assert s.total == 2
