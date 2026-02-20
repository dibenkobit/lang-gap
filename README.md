# LangBench: EN vs RU LLM Benchmark

Measures how much quality frontier LLMs lose when prompted in Russian instead of English. ~100 original questions (50 coding, 50 reasoning) are sent to each model twice — once in English, once in Russian — and the accuracy delta is the benchmark's output.

## Why

- **MERA** tests Russian-only (no English baseline to compare against)
- **MMLU-ProX** excludes Claude and Gemini
- **Global-MMLU-Lite** excludes Russian

None of these answer: "How much worse does model X perform in Russian vs English?"

## Models

All accessed via OpenRouter (temperature=0):

| Model | OpenRouter ID |
|-------|--------------|
| Claude Opus 4.6 | `anthropic/claude-opus-4-6` |
| Claude Sonnet 4.6 | `anthropic/claude-sonnet-4-6` |
| GPT-5.2 | `openai/gpt-5.2` |
| GPT-4.1 | `openai/gpt-4.1` |
| Gemini 2.5 Pro | `google/gemini-2.5-pro-preview-06-05` |
| DeepSeek R1 | `deepseek/deepseek-r1` |

## Setup

```bash
# Clone and install
cd lang-gap
cp .env.example .env
# Edit .env with your OpenRouter API key

# Install with uv
uv pip install -e .
# Or with pip
pip install -e .
```

## Usage

```bash
# Dry run — validate questions, show what would be sent
python -m lang_gap --dry-run

# Quick test — 5 questions on one model
python -m lang_gap --models gpt-4.1 --questions coding --limit 5

# Full run — all models, all questions
python -m lang_gap --models all --questions all

# Specific models and categories
python -m lang_gap --models claude-opus-4.6,gpt-5.2 --questions reasoning
```

Results are saved to `results/` (JSON) and reports to `reports/` (Markdown).

## Question Design

All questions are original (no existing benchmark contamination). Each has paired English and Russian prompts — the Russian is a natural re-statement, not a translation.

- **Coding** (50 questions): Python function implementation, 15 easy / 20 medium / 15 hard
- **Reasoning** (50 questions): Math, logic, and analytical word problems, same distribution

## Cost

~1,200 API calls per full run. Estimated $25-35 depending on reasoning model token usage.
