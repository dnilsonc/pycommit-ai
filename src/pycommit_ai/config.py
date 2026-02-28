import configparser
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pycommit_ai.errors import KnownError

# Constants
BUILTIN_SERVICES = ["OPENAI", "GEMINI", "GROQ", "OPENROUTER"]

# General Defaults
DEFAULT_LOCALE = "en"
DEFAULT_GENERATE = 1
DEFAULT_TYPE = "conventional"
DEFAULT_MAX_LENGTH = 50
DEFAULT_TIMEOUT = 10000
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 1.0
DEFAULT_EXCLUDES = ["package-lock.json", "pnpm-lock.yaml", "*.lock", "*.lockb", "uv.lock", "poetry.lock"]


def _get_config_path() -> Path:
    """Get the path to the pycommit-ai configuration file."""
    # check environment variable
    if "PYCOMMIT_AI_CONFIG_PATH" in os.environ:
        return Path(os.environ["PYCOMMIT_AI_CONFIG_PATH"])

    # check standard XDG config home
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg_config_home) / "pycommit-ai" / "config.ini"


def read_config_file() -> configparser.ConfigParser:
    """Read and return the ConfigParser instance for the config file."""
    config_path = _get_config_path()
    parser = configparser.ConfigParser()
    
    # Do not convert keys to lowercase
    parser.optionxform = str
    
    if config_path.exists():
        parser.read(config_path, encoding='utf-8')
    
    return parser


def get_config(cli_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the fully resolved configuration, combining defaults, config file, 
    environment variables, and CLI overrides.
    """
    cli_overrides = cli_overrides or {}
    parser = read_config_file()
    
    config: Dict[str, Any] = {
        "locale": cli_overrides.get("locale") or parser.get("general", "locale", fallback=DEFAULT_LOCALE),
        "generate": int(cli_overrides.get("generate") or parser.get("general", "generate", fallback=DEFAULT_GENERATE)),
        "type": cli_overrides.get("type") or parser.get("general", "type", fallback=DEFAULT_TYPE),
        "maxLength": int(cli_overrides.get("maxLength") or parser.get("general", "maxLength", fallback=DEFAULT_MAX_LENGTH)),
        "timeout": int(cli_overrides.get("timeout") or parser.get("general", "timeout", fallback=DEFAULT_TIMEOUT)),
        "maxTokens": int(cli_overrides.get("maxTokens") or parser.get("general", "maxTokens", fallback=DEFAULT_MAX_TOKENS)),
        "temperature": float(cli_overrides.get("temperature") or parser.get("general", "temperature", fallback=DEFAULT_TEMPERATURE)),
        "topP": float(cli_overrides.get("topP") or parser.get("general", "topP", fallback=DEFAULT_TOP_P)),
        "systemPrompt": cli_overrides.get("systemPrompt") or parser.get("general", "systemPrompt", fallback=""),
        "systemPromptPath": cli_overrides.get("systemPromptPath") or parser.get("general", "systemPromptPath", fallback=""),
    }
    
    # Process excludes format (can be string or list)
    excludes_val = cli_overrides.get("excludes") or parser.get("general", "excludes", fallback=",".join(DEFAULT_EXCLUDES))
    if isinstance(excludes_val, str):
        config["excludes"] = [e.strip() for e in excludes_val.split(",") if e.strip()]
    else:
        config["excludes"] = excludes_val
    
    # Defaults depending on provider
    provider_defaults = {
        "GEMINI": {"model": "gemini-2.5-flash"},
        "OPENAI": {"model": "gpt-4o-mini", "url": "https://api.openai.com", "path": "/v1/chat/completions"},
        "GROQ": {"model": "llama3-8b-8192"},
        "OPENROUTER": {"model": "google/gemini-2.0-flash-001", "url": "https://openrouter.ai/api", "path": "/v1/chat/completions"},
    }

    # Extract services configs
    for service in BUILTIN_SERVICES:
        service_config = {}
        
        # Priority: CLI > Env > File > Default
        
        # 1. Default
        for k, v in provider_defaults.get(service, {}).items():
            service_config[k] = v
            
        # 2. File
        if parser.has_section(service):
            for k, v in parser.items(service):
                service_config[k] = v
                
        # 3. Env
        env_key = os.environ.get(f"{service}_API_KEY")
        if env_key:
            service_config["key"] = env_key
            
        # 4. CLI overrides (if they pass service specific overrides)
        for k, v in cli_overrides.items():
            if k.startswith(f"{service}."):
                prop = k.split(".", 1)[1]
                service_config[prop] = v
                
        # Ensure models are parsed as lists for easier handling if provided as CSV
        if "model" in service_config and isinstance(service_config["model"], str):
            service_config["model"] = [m.strip() for m in service_config["model"].split(",") if m.strip()]
            
        config[service] = service_config

    return config


def set_configs(key_values: List[tuple[str, str]]):
    """Set configuration key-value pairs and write to config file."""
    parser = read_config_file()
    
    for key, value in key_values:
        if "." in key:
            section, prop = key.split(".", 1)
            # Ensure section is uppercase for providers
            if section.upper() in BUILTIN_SERVICES:
                section = section.upper()
            
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, prop, value)
        else:
            if not parser.has_section("general"):
                parser.add_section("general")
            parser.set("general", key, value)
            
    config_path = _get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        parser.write(f)


def del_config(key: str):
    """Delete a configuration setting or section."""
    parser = read_config_file()
    
    if "." in key:
        section, prop = key.split(".", 1)
        if parser.has_section(section):
            parser.remove_option(section, prop)
            if not parser.items(section):
                parser.remove_section(section)
        else:
            raise KnownError(f"Config section not found: {section}")
    else:
        # Either a section name or a general property
        if parser.has_section(key):
            parser.remove_section(key)
        elif parser.has_section("general") and parser.has_option("general", key):
            parser.remove_option("general", key)
        else:
            raise KnownError(f"Config not found: {key}")
            
    config_path = _get_config_path()
    if config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            parser.write(f)
            

def list_configs():
    """List all configurations in INI format."""
    parser = read_config_file()
    
    config_str = ""
    for section in parser.sections():
        config_str += f"[{section}]\n"
        for key, value in parser.items(section):
            config_str += f"{key} = {value}\n"
        config_str += "\n"
        
    return config_str.strip()


def get_config_path_str() -> str:
    """Return the absolute path of the configuration file."""
    return str(_get_config_path().absolute())
