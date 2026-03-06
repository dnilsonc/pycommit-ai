# pycommit-ai

> AI-powered Git commit message generator — get meaningful, conventional commit messages from multiple AI providers simultaneously.

Inspired by [aicommit2](https://github.com/tak-bro/aicommit2), rewritten in Python.

## ✨ Features

- 🤖 **Multi-provider support** — Gemini, OpenAI, Groq, and OpenRouter
- 📝 **Conventional Commits & Gitmoji** — choose your preferred commit style
- 🌍 **Multilingual** — generate messages in any locale (e.g., `en`, `pt`, `es`)
- ⚡ **Concurrent generation** — queries all configured providers at once
- 🚀 **Pull Request Generation** — generates PR descriptions from branch diffs
- 🔧 **Flexible configuration** — INI file, environment variables, or CLI flags
- ⌨️ **Quick alias** — use `pyc` as a fast shortcut

## 📦 Installation

**Requirements:** Python ≥ 3.13, [uv](https://docs.astral.sh/uv/)

### Global Install

```bash
uv tool install git+https://github.com/dnilsonc/pycommit-ai.git
```
*(The `pycommit-ai` command and `pyc` short alias will be available globally)*

**Update/Uninstall:**
```bash
uv tool upgrade pycommit-ai
uv tool uninstall pycommit-ai
```

### Alternative methods

| Method | Command |
|--------|---------|
| **pipx** | `pipx install git+https://github.com/dnilsonc/pycommit-ai.git` |
| **pip** | `pip install git+https://github.com/dnilsonc/pycommit-ai.git` |
| **Local dev** | `git clone ... && cd pycommit-ai && uv sync` |

## 🚀 Quick Start

1. **Configure an AI provider (or multiple)**
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

2. **Stage your changes and run**
```bash
git add .
pycommit-ai
```

3. **Generate a Pull Request description**
```bash
pyc --pr
```
*(Optionally, set a custom PR template: `pyc config set PR.templatePath=~/my-pr-template.md`)*

## 🏳️ CLI Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--locale` | `-l` | Locale for the commit message (e.g., `pt`, `en`, `es`) |
| `--generate` | `-g` | Number of messages to generate per model |
| `--all` | `-a` | Stage all changed files before generating |
| `--type` | `-t` | Commit message style: `conventional` or `gitmoji` |
| `--confirm` | `-y` | Auto-commit with the first generated message (no prompt) |
| `--dry-run` | `-d` | Show generated messages without committing |
| `--copy` | `-c` | Copy the selected message to clipboard instead of committing |
| `--exclude` | `-x` | Files to exclude from the diff (can be used multiple times) |
| `--print-prompt` | `-p` | Don't use AI, just print and copy the generated prompt |

### Examples

```bash
pycommit-ai -g 3 -l pt             # 3 messages per model in Portuguese
pycommit-ai -a -t gitmoji -y       # Gitmoji, stage all, auto-commit
pycommit-ai -c                     # Copy message to clipboard instead of committing
pyc -x "*-lock.json"               # Exclude lock files from diff
pyc --pr                           # Generate a PR description
pyc --pr --print-prompt            # Print the prompt without calling the AI
```

> **Note:** Common lock files (`uv.lock`, `package-lock.json`, etc.) are excluded by default.

## ⚙️ Configuration

Configuration is stored in `~/.config/pycommit-ai/config.ini` (follows XDG).

### Config Commands

```bash
pycommit-ai config set KEY=VALUE          # Set a value
pycommit-ai config get KEY                # Get a value
pycommit-ai config list                   # List all keys
pycommit-ai config del KEY                # Delete a key
pycommit-ai config path                   # Show config file path
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
| `PR.template` | — | Custom PR template (inline markdown) |
| `PR.templatePath` | — | **Recommended:** Path to a `.md` custom PR template file |

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
