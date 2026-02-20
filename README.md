# lang-gap

**Do LLMs get dumber when you speak Russian?**

This benchmark measures exactly that. Same questions, same models, English vs Russian. The accuracy delta tells you how much each model degrades in a non-English language.

```
Model               EN        RU        Δ
──────────────────────────────────────────────
Claude Opus 4.6     94%       91%       −3%
GPT-4.1             88%       79%       −9%
DeepSeek R1         86%       83%       −3%
```
<sup>Illustrative — run the benchmark to get real numbers for your models.</sup>

100 original questions (50 coding, 50 reasoning), written from scratch. No recycled benchmarks, zero contamination risk.

## Quickstart

Requires **Python 3.11+**.

```bash
cp .env.example .env          # add your OpenRouter API key
pip install -e .
python -m lang_gap --dry-run  # validate setup, no API calls
python -m lang_gap --models gpt-4.1 --limit 5  # test run (~$0.50)
python -m lang_gap            # full run, all models (~$25-35)
```

## How it works

```
questions/*.yaml → OpenRouter API → extract answer → evaluate → report
  (EN + RU)        (temperature=0)   (code/ANSWER:)   (sandbox/compare)
```

1. Load paired questions from `questions/*.yaml` — each has `prompt_en` + `prompt_ru`
2. Send every prompt to every model via [OpenRouter](https://openrouter.ai) (temperature=0 for reproducibility)
3. **Coding**: extract code from response, run against test cases in a sandbox
4. **Reasoning**: extract `ANSWER:` tag, compare to expected value
5. Generate a report with EN accuracy, RU accuracy, and the gap

## Questions

| File | Count | What's inside |
|------|-------|---------------|
| `questions/coding.yaml` | 50 | Python problems, 4-6 test cases each |
| `questions/reasoning.yaml` | 50 | Math, logic, and analytical word problems |

Russian versions use Russian names and culturally neutral units — not machine-translated English. To add more questions, use the prompt in `prompts/question_writer.md` with any frontier model.

## Models

Configured in `src/lang_gap/config.py`. Currently:

Claude Opus 4.6 / Claude Sonnet 4.6 / GPT-5.2 / GPT-4.1 / Gemini 2.5 Pro / DeepSeek R1

Any model available on [OpenRouter](https://openrouter.ai) works — just add it to the `MODELS` dict.

## Output

Each run produces:

- **`results/<run-id>.json`** — raw evaluation data
- **`reports/<run-id>.md`** — markdown tables per category + overall, plus a list of specific questions where EN passed but RU failed

## Development

```bash
pip install -e ".[dev]"
pytest                  # fast tests only
pytest -m slow          # include 10s timeout tests
ruff check src tests
mypy src
```

## License

[Apache 2.0](LICENSE)
