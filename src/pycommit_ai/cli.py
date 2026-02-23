import concurrent.futures
import sys
from typing import List, Tuple

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.text import Text

from pycommit_ai.config import BUILTIN_SERVICES, del_config, get_config, get_config_path_str, list_configs, set_configs
from pycommit_ai.errors import AIServiceError, KnownError
from pycommit_ai.git import assert_git_repo, commit_changes, get_branch_name, get_staged_diff, run_git_command
from pycommit_ai.services.base import AIResponse, AIService
from pycommit_ai.services.gemini import GeminiService
from pycommit_ai.services.groq import GroqService
from pycommit_ai.services.openai_service import OpenAIService
from pycommit_ai.services.openrouter import OpenRouterService

console = Console()

BANNER_LINES = [
    r"                                          __  __                __",
    r"     ____  __  _________  ____ ___  ____ _(_)/ /_  ____  ______(_)",
    r"    / __ \/ / / / ___/ _ \/ __ `__ \/ __ `/ / __/ _____/ __ \/ / ",
    r"   / /_/ / /_/ / /__/  __/ / / / / / / / / / /_ _____/ /_/ / /  ",
    r"  / .___/\__, /\___/\___/_/ /_/ /_/_/ /_/_/\__/      \__,_/_/   ",
    r" /_/    /____/                                                   ",
]

# Gradient colors for each line of the banner (purple → cyan → green)
BANNER_COLORS = [
    "#b06cff",
    "#9b6cff",
    "#6c9bff",
    "#6cccff",
    "#6cffc8",
    "#6cff8c",
]


def print_banner():
    """Print a colorful ASCII art banner for pycommit-ai."""
    console.print()
    for line, color in zip(BANNER_LINES, BANNER_COLORS):
        styled = Text(line, style=f"bold {color}")
        console.print(styled)
    console.print()


def get_available_services(config: dict, diff, branch_name: str) -> List[AIService]:
    """Return an instantiated list of AI services that have API keys configured."""
    services = []
    
    if config.get("GEMINI", {}).get("key"):
        for model in config["GEMINI"].get("model", ["gemini-2.5-flash"]):
            services.append(GeminiService(config, config["GEMINI"], diff, model))
            
    if config.get("OPENAI", {}).get("key"):
        for model in config["OPENAI"].get("model", ["gpt-4o-mini"]):
            services.append(OpenAIService(config, config["OPENAI"], diff, model))
            
    if config.get("GROQ", {}).get("key"):
        for model in config["GROQ"].get("model", ["llama3-8b-8192"]):
            services.append(GroqService(config, config["GROQ"], diff, model))
            
    if config.get("OPENROUTER", {}).get("key"):
        for model in config["OPENROUTER"].get("model", ["google/gemini-2.0-flash-001"]):
            services.append(OpenRouterService(config, config["OPENROUTER"], diff, model))
            
    return services


@click.group(invoke_without_command=True)
@click.option("--locale", "-l", help="Locale to use for the commit message (e.g., pt, en)")
@click.option("--generate", "-g", type=int, help="Number of messages to generate per model")
@click.option("--all", "-a", "stage_all", is_flag=True, help="Stage all changed files before generating")
@click.option("--type", "-t", type=click.Choice(["conventional", "gitmoji", ""]), help="Type of commit message")
@click.option("--confirm", "-y", is_flag=True, help="Automatically commit with the first generated message avoiding prompts")
@click.option("--dry-run", "-d", is_flag=True, help="Only show the generated messages without committing")
@click.option("--exclude", "-x", multiple=True, help="Files to exclude from the diff")
@click.pass_context
def cli(ctx, locale, generate, stage_all, type, confirm, dry_run, exclude):
    """pycommit-ai — AI-generated Git commits."""
    if ctx.invoked_subcommand is not None:
        return

    print_banner()

    try:
        assert_git_repo()
        
        if stage_all:
            run_git_command(["add", "-A"])
            
        cli_overrides = {}
        if locale:
            cli_overrides["locale"] = locale
        if generate:
            cli_overrides["generate"] = generate
        if type is not None:
            cli_overrides["type"] = type
            
        config = get_config(cli_overrides)
        
        diff = get_staged_diff(exclude_files=list(exclude))
        if not diff or not diff.files:
            console.print("[yellow]No staged files found. Please stage files using `git add` and try again.[/yellow]")
            sys.exit(0)
            
        branch_name = get_branch_name()
        services = get_available_services(config, diff, branch_name)
        
        if not services:
            console.print("[red]No AI providers configured. Please set an API key using `pycommit-ai config set PROVIDER.key=YOUR_KEY`.[/red]")
            console.print("Supported providers: GEMINI, OPENAI, GROQ, OPENROUTER")
            sys.exit(1)
            
        responses: List[Tuple[str, AIResponse]] = []
        
        with console.status("[bold green]Generating commit messages...") as status:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_service = {
                    executor.submit(srv.generate_commit_messages): f"{srv.__class__.__name__.replace('Service', '')} ({srv.model_name})"
                    for srv in services
                }
                
                for future in concurrent.futures.as_completed(future_to_service):
                    srv_name = future_to_service[future]
                    try:
                        results = future.result()
                        for r in results:
                            responses.append((srv_name, r))
                        console.print(f"[green]✓[/green] Generated from {srv_name}")
                    except AIServiceError as e:
                        console.print(f"[red]✗[/red] Error from {srv_name}: {e}")
                    except Exception as e:
                        console.print(f"[red]✗[/red] Unexpected error from {srv_name}: {e}")
                        
        if not responses:
            console.print("[red]Failed to generate any commit messages.[/red]")
            sys.exit(1)
            
        if confirm:
            chosen_msg = responses[0][1].value
        else:
            choices = [
                Choice(
                    value=item.value,
                    name=f"[{srv_name}] {item.title}"
                )
                for srv_name, item in responses
            ]
            
            chosen_msg = inquirer.select(
                message="Pick a commit message to use:",
                choices=choices,
                instruction="(Use arrow keys or type to search)",
                vi_mode=True,
            ).execute()
            
        if dry_run:
            console.print("\n[bold]Dry run — Selected Message:[/bold]")
            console.print(chosen_msg)
        else:
            commit_changes(chosen_msg)
            console.print(f"\n[bold green]Successfully committed![/bold green]")
            
    except KnownError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        sys.exit(0)


@cli.group()
def config():
    """Manage configuration settings."""
    pass


@config.command("set")
@click.argument("key_values", nargs=-1, required=True)
def config_set(key_values):
    """Set configuration values (e.g. OPENAI.key=YOUR_KEY)."""
    try:
        parsed = []
        for kv in key_values:
            if "=" not in kv:
                raise KnownError(f"Invalid format for '{kv}'. Use: KEY=VALUE")
            k, v = kv.split("=", 1)
            parsed.append((k, v))
        set_configs(parsed)
        console.print("[green]Configuration saved successfully.[/green]")
    except KnownError as e:
        console.print(f"[red]Error:[/red] {e}")


@config.command("get")
@click.argument("keys", nargs=-1)
def config_get(keys):
    """Retrieve configuration values by key."""
    try:
        conf = get_config()
        if not keys:
            console.print(conf)
            return
            
        for k in keys:
            parts = k.split(".")
            val = conf
            found = True
            for p in parts:
                if p in val:
                    val = val[p]
                else:
                    found = False
                    break
            if found:
                console.print(f"{k} = {val}")
            else:
                console.print(f"[yellow]{k} not found[/yellow]")
    except KnownError as e:
        console.print(f"[red]Error:[/red] {e}")


@config.command("list")
def config_list():
    """Display all configuration keys and their values."""
    try:
        console.print(list_configs())
    except KnownError as e:
        console.print(f"[red]Error:[/red] {e}")


@config.command("del")
@click.argument("key")
def config_del(key):
    """Delete a configuration setting or section."""
    try:
        del_config(key)
        console.print(f"[green]Successfully deleted config: {key}[/green]")
    except KnownError as e:
        console.print(f"[red]Error:[/red] {e}")


@config.command("path")
def config_path():
    """Display the path of the loaded configuration file."""
    console.print(get_config_path_str())


def main():
    cli()


if __name__ == "__main__":
    main()
