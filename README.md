# lang-gap

Sends the same questions to LLMs in English and Russian, compares accuracy. The gap tells you how much a model degrades in Russian.

100 original questions (50 coding, 50 reasoning). No recycled benchmarks — everything written from scratch to avoid contamination.

## How it works

1. Load questions from `questions/*.yaml` (each has `prompt_en` + `prompt_ru`)
2. Send each prompt to each model via OpenRouter (temperature=0)
3. For coding: extract code, run against test cases in a sandbox
4. For reasoning: extract `ANSWER:` from response, compare to expected
5. Print a table showing EN accuracy, RU accuracy, and the delta

## Run it

```
cp .env.example .env        # put your OpenRouter key there
pip install -e .             # install deps
python -m lang_gap --dry-run # check everything loads, no API calls
python -m lang_gap --models gpt-4.1 --limit 5  # cheap test run
python -m lang_gap           # full run, all models, ~$25-35
```

## Models

Edit `src/lang_gap/config.py` to add/remove. Currently:

Claude Opus 4.6, Claude Sonnet 4.6, GPT-5.2, GPT-4.1, Gemini 2.5 Pro, DeepSeek R1

## Output

`results/` — raw JSON (one file per run, gitignored)
`reports/` — markdown tables like:

```
Model           | EN    | RU    | Δ
Claude Opus 4.6 | 90%   | 87%   | -3%
GPT-4.1         | 85%   | 78%   | -7%
```

Plus a list of specific questions where EN passed but RU failed.

## Questions

`questions/coding.yaml` — 50 Python problems, 4-6 test cases each
`questions/reasoning.yaml` — 50 math/logic/analytical word problems

To add more, use the prompt in `prompts/question_writer.md` with any frontier model.
