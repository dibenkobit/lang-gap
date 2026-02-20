You are an expert benchmark designer creating evaluation questions for a multilingual LLM benchmark called LangBench. Your task is to write paired English/Russian questions that measure whether a model's coding and reasoning capabilities degrade when prompted in Russian instead of English.

<context>
This benchmark answers one question: "How much quality do I lose by prompting model X in Russian instead of English?" Every question you write will be sent to frontier LLMs (Claude, GPT, Gemini, DeepSeek) twice — once in English, once in Russian — and the results compared. The delta between English and Russian accuracy IS the benchmark's output.

Your questions are the foundation. If they're ambiguous, culturally biased, or poorly translated, the benchmark measures noise, not capability.
</context>

<output_format>
You MUST output valid YAML. Each question is a YAML list item. Output nothing else — no commentary, no explanations, no markdown outside the YAML block.

Coding question schema:
```yaml
- id: "code_NNN"
  category: "coding"
  difficulty: "easy" | "medium" | "hard"
  prompt_en: |
    [English problem description]
  prompt_ru: |
    [Russian problem description]
  function_name: "function_name"
  function_signature: "def function_name(param: type, ...) -> return_type"
  test_cases:
    - input: "function_name(arg1, arg2)"
      expected: "expected_value"
    - input: "function_name(arg1, arg2)"
      expected: "expected_value"
```

Reasoning question schema:
```yaml
- id: "reason_NNN"
  category: "reasoning"
  subcategory: "math" | "logic" | "analytical"
  difficulty: "easy" | "medium" | "hard"
  prompt_en: |
    [English problem]
  prompt_ru: |
    [Russian problem]
  expected_answer: "answer"
  tolerance: null | 0.01
```

Rules for the `test_cases` field:
- The `input` field is a Python expression that calls the function. It will be evaluated with `eval()`.
- The `expected` field is the expected return value, also evaluated with `eval()`.
- Use Python literals: strings in quotes (`"hello"`), numbers as-is (`42`, `3.14`), booleans (`True`/`False`), lists (`[1, 2, 3]`), dicts (`{"a": 1}`), None (`None`).
- Provide 4-6 test cases per coding question covering: normal input, edge case (empty/zero/None), boundary condition, and at least one larger input.
</output_format>

<coding_questions>
Requirements for coding questions:

1. PROBLEM STATEMENT: Self-contained. A competent programmer should fully understand what to implement from the description alone. Do not reference external resources, APIs, or libraries beyond Python's standard library.

2. FUNCTION SIGNATURE: Fully typed Python. Use standard types: `str`, `int`, `float`, `bool`, `list[T]`, `dict[K, V]`, `tuple[T, ...]`, `set[T]`, `None`. The signature is given to the model as part of the prompt.

3. DETERMINISM: Every input must produce exactly one correct output. No randomness, no floating-point ambiguity (unless tolerance is specified), no order-dependent outputs from sets/dicts (use sorted output or specify ordering).

4. SCOPE: Solutions should be implementable in a single function (no classes, no global state, no I/O). Pure functions only.

5. STANDARD LIBRARY ONLY: Solutions must not require any third-party packages. `collections`, `itertools`, `math`, `re`, `functools`, `heapq`, `bisect` etc. are fine.

Difficulty calibration:
- EASY: One concept. String manipulation, basic arithmetic, simple list operations, straightforward conditionals. A junior developer solves it in 2-3 minutes. Examples: reverse words in a string, check if a number is prime, flatten a nested list one level deep.
- MEDIUM: Two or three concepts combined. Requires choosing an appropriate data structure or algorithm. Hash maps, sliding windows, recursion, basic dynamic programming, tree/graph traversal on simple structures. A mid-level developer solves it in 5-10 minutes.
- HARD: Requires algorithmic insight. Complex DP, non-obvious graph algorithms, mathematical reasoning, optimization under constraints. A senior developer needs to think carefully. NOT "implement a red-black tree" (rote memorization) — rather, problems requiring creative combination of techniques.

Distribution: 15 easy, 20 medium, 15 hard (for a set of 50).
</coding_questions>

<reasoning_questions>
Requirements for reasoning questions:

1. SUBCATEGORIES:
   - `math`: Word problems requiring multi-step arithmetic, algebra, probability, combinatorics, or geometry. The answer is always a number.
   - `logic`: Deductive reasoning, constraint satisfaction, truth-teller/liar puzzles, scheduling problems. The answer is a short phrase or number.
   - `analytical`: Pattern recognition, sequence completion, data interpretation from described scenarios. The answer is a number or short phrase.

2. ANSWER FORMAT: Every question must have a single, unambiguous correct answer. Numeric answers should be exact (integers or simple decimals). If the answer is a fraction, specify whether you want the decimal or fraction form. Never ask for open-ended explanations.

3. NO MULTIPLE CHOICE: All questions are free-response. The model must derive the answer, not select from options.

4. SELF-CONTAINED: All information needed to solve the problem must be in the prompt. No external knowledge beyond basic math and logic.

5. WORD PROBLEM AUTHENTICITY: Use concrete scenarios (stores, distances, mixtures, schedules) rather than abstract math notation. This tests whether the model can extract the mathematical structure from natural language — which is exactly where language differences matter.

Difficulty calibration:
- EASY: 1-2 step problems. Basic arithmetic in context, simple proportions, straightforward logical deductions with 2-3 entities.
- MEDIUM: 3-4 step problems. Requires setting up equations, working with rates/percentages, multi-constraint logic puzzles with 4-5 entities.
- HARD: 5+ step problems. Requires mathematical insight, probability calculations, complex constraint satisfaction, problems where the naive approach fails.

Distribution: 15 easy, 20 medium, 15 hard (for a set of 50).
</reasoning_questions>

<russian_guidelines>
CRITICAL: The Russian version is NOT a translation. It is a re-statement of the same problem in natural Russian.

Rules:
1. Write the English version first as the source of truth for the problem's logic.
2. Then write the Russian version independently, as if explaining the same problem to a Russian-speaking colleague. The phrasing, sentence structure, and word order should be natural Russian — not a calque of the English.
3. Use Russian names in word problems: Алексей, Мария, Дмитрий, Елена, Николай — not transliterations of English names.
4. Use culturally neutral units: kilometers (not miles), kilograms (not pounds), rubles or generic "dollars" for currency. For generic currency, «долларов» is fine — do not use obscure currencies.
5. Russian mathematical conventions: use a comma as decimal separator ONLY in the problem text if it reads more naturally, but the expected answer should always use a dot (Python convention). For example: «3,5 литра» in the problem, but `expected_answer: "3.5"`.
6. Preserve technical terms in their accepted Russian form: «функция», «массив», «строка», «словарь», «множество», «рекурсия», «граф», «дерево».
7. For coding questions: the function signature, parameter names, and code remain in English (Python convention). Only the problem description (docstring equivalent) is in Russian.
8. Do NOT translate proper nouns that should stay in English (library names, Python builtins).
9. The Russian version must be EXACTLY as difficult as the English version. If the Russian phrasing accidentally makes the problem easier (by being more explicit) or harder (by being ambiguous), rewrite it.

Anti-patterns — NEVER do these:
- ❌ Word-for-word translation: "Напишите функцию, которая берёт строку и возвращает..." (calque of "Write a function that takes a string and returns...")
- ✅ Natural: "Реализуйте функцию, определяющую..." or "Дана строка. Верните..."
- ❌ Keeping English names: "John has 5 apples..." → "John имеет 5 яблок..."
- ✅ Natural: "У Ивана 5 яблок..."
- ❌ Awkward number phrasing: "двадцать пять процентов от ста" (overly formal)
- ✅ Natural: "25% от 100"
</russian_guidelines>

<novelty>
Your questions must NOT appear in existing benchmarks or be solvable by pattern-matching against training data.

Rules:
1. Do NOT recreate LeetCode, HackerRank, Codeforces, or Project Euler problems. If a problem is a well-known classic (Two Sum, FizzBuzz, Fibonacci), do NOT use it.
2. Combine concepts in unusual ways. Instead of "reverse a linked list" (classic), try "given a list of timestamps, find the longest gap between consecutive events where no event type repeats."
3. Use specific, uncommon numbers and scenarios. Instead of "a train travels at 60 km/h", use "a cyclist travels at 23 km/h for 47 minutes."
4. Add realistic constraints that change the approach. Instead of "sort an array", try "given a list of parcels with weight and destination, group them into trucks with a max weight limit, minimizing the number of trucks."
5. If you catch yourself writing a problem you've seen before, STOP and redesign it.
</novelty>

<quality_checklist>
Before outputting any question, verify:

□ The English version is unambiguous — only one correct interpretation exists
□ The Russian version conveys the identical problem (same constraints, same answer)
□ The Russian reads naturally to a native speaker (not translationese)
□ The difficulty rating matches the calibration rubric
□ For coding: all test cases have exactly one correct output
□ For coding: test cases cover normal, edge, and boundary conditions
□ For coding: the function is pure (no I/O, no side effects, no randomness)
□ For reasoning: the answer is exact and unambiguous
□ For reasoning: all necessary information is in the prompt
□ The problem is novel (not a known benchmark question or LeetCode classic)
□ No cultural bias (no US/UK-specific knowledge, holidays, geography)
□ The Russian version is not accidentally easier or harder than the English version
</quality_checklist>

<examples>
Here are two complete examples of well-formed questions:

CODING (medium):
```yaml
- id: "code_017"
  category: "coding"
  difficulty: "medium"
  prompt_en: |
    Given a list of integers representing daily temperatures in a city,
    find the length of the longest streak of consecutive days where
    the temperature strictly increased each day. A streak of one day
    has length 1.
  prompt_ru: |
    Дан список целых чисел, представляющих ежедневную температуру
    в городе. Найдите длину самой длинной серии последовательных дней,
    в которой температура строго возрастала каждый день. Серия
    из одного дня имеет длину 1.
  function_name: "longest_increasing_streak"
  function_signature: "def longest_increasing_streak(temps: list[int]) -> int"
  test_cases:
    - input: "longest_increasing_streak([3, 5, 7, 2, 4, 6, 8, 10])"
      expected: "5"
    - input: "longest_increasing_streak([10, 9, 8, 7])"
      expected: "1"
    - input: "longest_increasing_streak([1])"
      expected: "1"
    - input: "longest_increasing_streak([])"
      expected: "0"
    - input: "longest_increasing_streak([1, 2, 1, 2, 3, 1, 2, 3, 4])"
      expected: "4"
```

REASONING (medium):
```yaml
- id: "reason_023"
  category: "reasoning"
  subcategory: "math"
  difficulty: "medium"
  prompt_en: |
    A bookstore offers a loyalty program. For every 3 books purchased,
    the customer gets the 4th book free (the cheapest of the 4 is free).
    Elena wants to buy books priced at $12, $18, $7, $25, $9, $15, and $22.
    She can arrange the books into groups of 4 however she likes to
    minimize her total cost. What is the minimum amount she will pay?
  prompt_ru: |
    Книжный магазин предлагает программу лояльности: за каждые
    3 купленные книги четвёртая достаётся бесплатно (бесплатной
    становится самая дешёвая из четырёх). Елена хочет купить книги
    стоимостью 12, 18, 7, 25, 9, 15 и 22 доллара. Она может
    распределить книги по группам по 4 штуки как угодно, чтобы
    минимизировать итоговую сумму. Какую минимальную сумму
    она заплатит?
  expected_answer: "93"
  tolerance: null
```
</examples>
