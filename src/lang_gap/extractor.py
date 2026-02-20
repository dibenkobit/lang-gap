"""Extract code blocks and answers from raw LLM responses."""

import re


def extract_code(response: str, function_name: str) -> str | None:
    """Extract a Python function from an LLM response.

    Strategy:
    1. Find ```python fenced blocks; prefer the one containing `def function_name`.
    2. If no fenced block, look for `def function_name` in raw text.
    """
    # Collect all ```python blocks
    blocks: list[str] = re.findall(
        r"```(?:python|py)\s*\n(.*?)```", response, re.DOTALL
    )

    if blocks:
        # Prefer the block that contains the target function
        for block in blocks:
            if f"def {function_name}" in block:
                return block.strip()
        # Fallback: return the first block
        return blocks[0].strip()

    # No fenced block — try to find the function in raw text
    pattern = rf"(def {re.escape(function_name)}\(.*\n(?:[ \t]+.+\n)*)"
    m = re.search(pattern, response)
    if m:
        return m.group(0).strip()

    return None


def extract_answer(response: str) -> str | None:
    """Extract a reasoning answer from an LLM response.

    Looks for "ANSWER: <value>" (last occurrence, case-insensitive).
    Falls back to extracting the last number in the response.
    """
    # Last occurrence of ANSWER: ...
    matches: list[str] = re.findall(
        r"ANSWER:\s*(.+?)$", response, re.MULTILINE | re.IGNORECASE
    )
    if matches:
        return matches[-1].strip()

    # Fallback: last number (int or float) in the response
    numbers: list[str] = re.findall(r"-?\d+(?:\.\d+)?", response)
    if numbers:
        return numbers[-1]

    return None
