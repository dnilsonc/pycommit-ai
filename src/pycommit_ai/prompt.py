import re
from pathlib import Path
from typing import Any, Dict, Optional

from pycommit_ai.errors import KnownError

DEFAULT_PROMPT_OPTIONS: Dict[str, Any] = {
    "locale": "en",
    "maxLength": 50,
    "type": "conventional",
    "generate": 1,
    "systemPrompt": "",
    "systemPromptPath": "",
}

COMMIT_TYPE_FORMATS = {
    "": "<commit message>",
    "conventional": "<type>(<optional scope>): <description>",
    "gitmoji": ":<emoji>:(<optional scope>): <description>",
}

COMMIT_TYPES = {
    "": "",
    "gitmoji": "\n" + "\n".join([
        "  - :sparkles:: Introduce new features.",
        "  - :bug:: Fix a bug.",
        "  - :memo:: Add or update documentation.",
        "  - :art:: Improve structure / format of the code.",
        "  - :zap:: Improve performance.",
        "  - :fire:: Remove code or files.",
        "  - :ambulance:: Critical hotfix.",
        "  - :white_check_mark:: Add, update, or pass tests.",
        "  - :lock:: Fix security or privacy issues.",
        "  - :rocket:: Deploy stuff.",
        "  - :lipstick:: Add or update the UI and style files.",
        "  - :tada:: Begin a project.",
        "  - :recycle:: Refactor code.",
        "  - :wrench:: Add or update configuration files.",
        "  - :bulb:: Add or update comments in source code.",
        "  - :twisted_rightwards_arrows:: Merge branches.",
    ]),
    "conventional": "\n" + "\n".join([
        "  - docs: Documentation only changes",
        "  - style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)",
        "  - refactor: A code change that neither fixes a bug nor adds a feature",
        "  - perf: A code change that improves performance",
        "  - test: Adding missing tests or correcting existing tests",
        "  - build: Changes that affect the build system or external dependencies",
        "  - ci: Changes to CI configuration files, scripts",
        "  - chore: Other changes that don't modify src or test files",
        "  - revert: Reverts a previous commit",
        "  - feat: A new feature",
        "  - fix: A bug fix",
    ]),
}

def parse_template(template: str, options: Dict[str, Any]) -> str:
    def replace_match(match) -> str:
        key = match.group(1)
        val = options.get(key)
        if val is None:
            val = DEFAULT_PROMPT_OPTIONS.get(key, "")
        return str(val)

    return re.sub(r"\{(\w+)\}", replace_match, template)

def get_localized_example(commit_type: str, locale: str) -> Dict[str, str]:
    base_locale = locale.split("-")[0].lower()
    
    examples = {
        "conventional": {
            "en": {
                "subject": "fix(auth): fix bug in user authentication process",
                "body": "- Update login function to handle edge cases\\n- Add additional error logging for debugging",
            },
            "pt": {
                "subject": "fix(auth): corrigir erro no processo de autenticação de usuário",
                "body": "- Atualizar função de login para lidar com casos extremos\\n- Adicionar log de erros adicional para depuração",
            }
        },
        "gitmoji": {
            "en": {
                "subject": ":sparkles: Add real-time chat feature",
                "body": "- Implement WebSocket connection\\n- Add message encryption\\n- Include typing indicators",
            },
            "pt": {
                "subject": ":sparkles: Adicionar recurso de chat em tempo real",
                "body": "- Implementar conexão WebSocket\\n- Adicionar criptografia de mensagens\\n- Incluir indicadores de digitação",
            }
        },
        "": {
            "en": {"subject": "", "body": ""}
        }
    }
    
    type_examples = examples.get(commit_type, examples[""])
    return type_examples.get(base_locale, type_examples.get("en", {"subject": "", "body": ""}))

def default_prompt(options: Dict[str, Any]) -> str:
    commit_type = options.get("type", "conventional")
    max_length = options.get("maxLength", 50)
    generate = options.get("generate", 1)
    locale = options.get("locale", "en")
    
    msg_plural = "s" if generate != 1 else ""
    
    lines = [
        "You are an expert Git commit message writer specializing in analyzing code changes and creating precise, meaningful commit messages.",
        f"Your task is to generate exactly {generate} {commit_type} style commit message{msg_plural} based on the provided git diff.",
        "",
        "## Requirements:",
        f"1. Language: Write all messages in {locale}",
        f"2. Format: Strictly follow the {commit_type} commit format:",
        COMMIT_TYPE_FORMATS.get(commit_type, ""),
        f"3. Allowed Types:{COMMIT_TYPES.get(commit_type, '')}",
        "",
        "## Guidelines:",
        f"- Subject line: Max {max_length} characters, imperative mood, no period",
        "- Analyze the diff to understand:",
        "  * What files were changed",
        "  * What functionality was added, modified, or removed",
        "  * The scope and impact of changes",
        "- For the commit type, choose based on:",
        "  * feat: New functionality or feature",
        "  * fix: Bug fixes or error corrections",
        "  * refactor: Code restructuring without changing functionality",
        "  * docs: Documentation changes only",
        "  * style: Formatting, missing semi-colons, etc",
        "  * test: Adding or modifying tests",
        "  * chore: Maintenance tasks, dependency updates",
        "  * perf: Performance improvements",
        "  * build: Build system or external dependency changes",
        "  * ci: CI configuration changes",
        "- Scope: Extract from file paths or logical grouping (e.g., auth, api, ui)",
        "",
        "## Important:",
        "- Keep messages short and concise — subject line only, no body or footer.",
        "- Focus on WHAT changed, not detailed explanations.",
    ]
    
    return "\n".join(lines)

def final_prompt(commit_type: str, generate: int, locale: str) -> str:
    msg_plural = "s" if generate != 1 else ""
    
    def get_example(ctype: str) -> str:
        loc_example = get_localized_example(ctype, locale)
        if ctype in ["conventional", "gitmoji"]:
            example_objs = []
            for _ in range(generate):
                example_objs.append(
                    '  {\n' +
                    f'    "subject": "{loc_example["subject"]}"\n' +
                    '  }'
                )
            return ",\n".join(example_objs)
        return ""
    
    lines = [
        f"\nProvide your response as a JSON array containing exactly {generate} object{msg_plural}, each with the following key:",
        f'- "subject": The commit message using the {commit_type} style. Concise, max one line.',
        f"The array must always contain {generate} element{msg_plural}, no more and no less.",
        f"Example response format: \n[\n{get_example(commit_type)}\n]",
        "The response must be valid, parseable JSON. Do NOT include body or footer fields."
    ]
    
    return "\n".join(lines)

def generate_prompt(options: Dict[str, Any]) -> str:
    system_prompt_str = options.get("systemPrompt")
    system_prompt_path = options.get("systemPromptPath")
    commit_type = options.get("type", "conventional")
    generate = options.get("generate", 1)
    locale = options.get("locale", "en")
    
    if system_prompt_str:
        base = parse_template(system_prompt_str, options)
        return f"{base}\n{final_prompt(commit_type, generate, locale)}"
        
    if system_prompt_path:
        path = Path(system_prompt_path).expanduser().resolve()
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            base = parse_template(content, options)
            return f"{base}\n{final_prompt(commit_type, generate, locale)}"
        except Exception:
            pass
            
    base = default_prompt(options)
    return f"{base}\n{final_prompt(commit_type, generate, locale)}"

def generate_user_prompt(diff: str) -> str:
    return (
        "Please analyze the following diff and generate commit message(s) based on the changes:\n\n"
        f"```diff\n{diff}\n```\n\n"
        "Focus on understanding the purpose and impact of these changes to create meaningful commit message(s)."
    )
