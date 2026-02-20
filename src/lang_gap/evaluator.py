"""Execute extracted code and check answers."""

import math
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from lang_gap.schemas import CodingQuestion, TestCase


def evaluate_coding(code: str, question: CodingQuestion) -> tuple[bool, str | None]:
    """Run extracted code against test cases in a subprocess.

    Returns (all_passed, error_message_or_none).
    """
    harness = _build_test_harness(code, question.function_name, question.test_cases)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as tmp:
        tmp.write(harness)
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [sys.executable, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, "Execution timed out (10s)"
    finally:
        tmp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Truncate long tracebacks
        if len(stderr) > 500:
            stderr = stderr[:500] + "..."
        return False, f"Runtime error: {stderr}"

    stdout = result.stdout.strip()
    lines = stdout.splitlines()

    failures: list[str] = []
    for line in lines:
        if line.startswith("FAIL:"):
            failures.append(line)

    if failures:
        return False, "; ".join(failures)

    if not any(line.startswith("PASS:") for line in lines):
        return False, f"No test output detected. stdout: {stdout[:200]}"

    return True, None


def _build_test_harness(
    code: str, function_name: str, test_cases: list[TestCase]
) -> str:
    """Generate a self-contained test script."""
    parts = [code, "", "# --- test harness ---", "import math", ""]

    for i, tc in enumerate(test_cases):
        parts.append(
            textwrap.dedent(f"""\
            try:
                _result_{i} = {tc.input}
                _expected_{i} = {tc.expected}
                if _result_{i} == _expected_{i}:
                    print("PASS: case {i}")
                else:
                    print(f"FAIL: case {i}: got {{_result_{i}!r}}, expected {{_expected_{i}!r}}")
            except Exception as _e_{i}:
                print(f"FAIL: case {i}: exception {{_e_{i}}}")
            """)
        )

    return "\n".join(parts)


def evaluate_reasoning(
    extracted: str, expected: str, tolerance: float | None
) -> bool:
    """Compare extracted answer to expected answer."""
    extracted_norm = extracted.strip().lower()
    expected_norm = expected.strip().lower()

    if extracted_norm == expected_norm:
        return True

    # Try numeric comparison
    try:
        e_val = float(extracted_norm)
        x_val = float(expected_norm)
        tol = tolerance if tolerance is not None else 0.0
        return math.isclose(e_val, x_val, abs_tol=tol)
    except ValueError:
        pass

    return False
