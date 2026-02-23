# pycommit-ai

> AI-powered Git commit message generator — get meaningful, conventional commit messages from multiple AI providers simultaneously.

Inspired by [aicommit2](https://github.com/tak-bro/aicommit2), rewritten in Python.

## ✨ Features

- 🤖 **Multi-provider support** — Gemini, OpenAI, Groq, and OpenRouter running in parallel
- 📝 **Conventional Commits & Gitmoji** — choose your preferred commit style
- 🌍 **Multilingual** — generate messages in any locale (e.g., `en`, `pt`, `es`)
- ⚡ **Concurrent generation** — queries all configured providers at once
- 🎨 **Interactive selection** — pick the best message from all suggestions
- 🔧 **Flexible configuration** — INI file, environment variables, or CLI flags

## 📦 Installation

**Requirements:** Python ≥ 3.13, [uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone https://github.com/your-user/pycommit-ai.git
cd pycommit-ai

# Install with uv
uv sync
```

Or install directly with pip:

```bash
pip install .
```

## 🚀 Quick Start

### 1. Configure an AI provider

```bash
# Gemini (default model: gemini-2.5-flash)
pycommit-ai config set GEMINI.key=YOUR_GEMINI_API_KEY

# OpenAI (default model: gpt-4o-mini)
pycommit-ai config set OPENAI.key=YOUR_OPENAI_API_KEY

# Groq (default model: llama3-8b-8192)
pycommit-ai config set GROQ.key=YOUR_GROQ_API_KEY

# OpenRouter (default model: google/gemini-2.0-flash-001)
pycommit-ai config set OPENROUTER.key=YOUR_OPENROUTER_API_KEY
```

You can configure **multiple providers** — they will all run in parallel.

### 2. Stage your changes and run

```bash
git add .
pycommit-ai
```

Or stage everything automatically:

```bash
pycommit-ai --all
```

## 🏳️ CLI Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--locale` | `-l` | Locale for the commit message (e.g., `pt`, `en`, `es`) |
| `--generate` | `-g` | Number of messages to generate per model |
| `--all` | `-a` | Stage all changed files before generating |
| `--type` | `-t` | Commit message style: `conventional` or `gitmoji` |
| `--confirm` | `-y` | Auto-commit with the first generated message (no prompt) |
| `--dry-run` | `-d` | Show generated messages without committing |
| `--exclude` | `-x` | Files to exclude from the diff (can be used multiple times) |

### Examples

```bash
# Generate 3 messages per model in Portuguese
pycommit-ai -g 3 -l pt

# Gitmoji style, stage all, dry run
pycommit-ai -a -t gitmoji -d

# Auto-commit with the first suggestion
pycommit-ai -y

# Exclude lock files from the diff
pycommit-ai -x uv.lock -x package-lock.json
```

## ⚙️ Configuration

Configuration is stored in `~/.config/pycommit-ai/config.ini` (follows XDG).

### Config Commands

```bash
# Set a value
pycommit-ai config set KEY=VALUE

# Set a provider-specific value
pycommit-ai config set GEMINI.model=gemini-2.5-pro

# Get a value
pycommit-ai config get GEMINI.model

# List all configuration
pycommit-ai config list

# Delete a setting
pycommit-ai config del GEMINI.model

# Show config file path
pycommit-ai config path
```

### Available Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `locale` | `en` | Language for generated messages |
| `generate` | `1` | Number of messages per model |
| `type` | `conventional` | Commit style (`conventional` / `gitmoji`) |
| `maxLength` | `50` | Max character length for the subject line |
| `timeout` | `10000` | Request timeout in milliseconds |
| `maxTokens` | `2048` | Max tokens for AI response |
| `temperature` | `0.7` | AI creativity (0.0 – 1.0) |
| `topP` | `1.0` | Nucleus sampling parameter |
| `systemPrompt` | — | Custom system prompt (inline) |
| `systemPromptPath` | — | Path to a custom system prompt file |

### Provider Settings

Each provider supports `key` and `model` (comma-separated for multiple models):

```bash
# Use multiple models for a single provider
pycommit-ai config set OPENAI.model=gpt-4o,gpt-4o-mini

# Custom API URL (OpenAI-compatible endpoints)
pycommit-ai config set OPENAI.url=https://your-custom-api.com
pycommit-ai config set OPENAI.path=/v1/chat/completions
```

### Environment Variables

API keys can also be set via environment variables:

```bash
export GEMINI_API_KEY=your-key
export OPENAI_API_KEY=your-key
export GROQ_API_KEY=your-key
export OPENROUTER_API_KEY=your-key
```

Use `PYCOMMIT_AI_CONFIG_PATH` to override the config file location:

```bash
export PYCOMMIT_AI_CONFIG_PATH=/path/to/custom/config.ini
```

### Config Priority

Settings are resolved in this order (highest priority first):

1. **CLI flags** (`--locale`, `--generate`, etc.)
2. **Environment variables** (`GEMINI_API_KEY`, etc.)
3. **Config file** (`~/.config/pycommit-ai/config.ini`)
4. **Defaults**

## 🧪 Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest -v

# Run the CLI locally
uv run pycommit-ai --help
```

## 📄 License

MIT
