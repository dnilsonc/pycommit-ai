import sys
from typing import List, Tuple

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.text import Text

from pycommit_ai.config import del_config, get_config, get_config_path_str, list_configs, set_configs
from pycommit_ai.core import generate_commits_parallel, generate_pr_description
from pycommit_ai.errors import KnownError
from pycommit_ai.git import assert_git_repo, commit_changes, get_branch_commits, get_branch_name, get_merge_base_diff, get_staged_diff, run_git_command
from pycommit_ai.services import AIResponse, get_available_services
from pycommit_ai.utils import copy_to_clipboard

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


def _handle_pr_command(locale: str = None, print_prompt: bool = False):
    """Facade for the PR generation interaction."""
    locale = locale or "en"
    config = get_config()
    branch = get_branch_name()

    console.print(f"[bold]Generating PR description for branch:[/bold] {branch}\n")

    diff = get_merge_base_diff(config_exclude=config.get("excludes", []))

    file_count = len(diff.files)
    file_word = "file" if file_count == 1 else "files"
    console.print(f"[green]✓[/green] [bold]{file_count} changed {file_word}:[/bold]")
    for f in diff.files:
        console.print(f"      {f}")
    console.print()

    commits = get_branch_commits()
    console.print(f"[green]✓[/green] [bold]{len(commits)} commit(s) in branch[/bold]")
    for c in commits:
        console.print(f"      • {c}")
    console.print()

    if print_prompt:
        pr_text = generate_pr_description(config, branch, diff, commits, locale, print_prompt=True)
        copy_to_clipboard(pr_text)
        console.print("[bold green]PR prompt copied to clipboard![/bold green]\n")
        console.print(pr_text)
    else:
        with console.status("[bold green]Generating PR description..."):
            pr_text = generate_pr_description(config, branch, diff, commits, locale)

        copy_to_clipboard(pr_text)
        console.print("[bold green]PR description copied to clipboard![/bold green]\n")
        console.print(pr_text)


@click.group(invoke_without_command=True)
@click.option("--locale", "-l", help="Locale to use for the commit message (e.g., pt, en)")
@click.option("--generate", "-g", type=int, help="Number of messages to generate per model")
@click.option("--all", "-a", "stage_all", is_flag=True, help="Stage all changed files before generating")
@click.option("--type", "-t", type=click.Choice(["conventional", "gitmoji", ""]), help="Type of commit message")
@click.option("--confirm", "-y", is_flag=True, help="Automatically commit with the first generated message avoiding prompts")
@click.option("--dry-run", "-d", is_flag=True, help="Only show the generated messages without committing")
@click.option("--copy", "-c", is_flag=True, help="Copy the selected message to clipboard instead of committing")
@click.option("--pr", is_flag=True, help="Generate a PR description from the current branch and copy to clipboard")
@click.option("--exclude", "-x", multiple=True, help="Files to exclude from the diff")
@click.option("--print-prompt", "-p", is_flag=True, help="Don't use AI, just print and copy the generated prompt")
@click.pass_context
def cli(ctx, locale, generate, stage_all, type, confirm, dry_run, copy, pr, exclude, print_prompt):
    """pycommit-ai — AI-generated Git commits."""
    if ctx.invoked_subcommand is not None:
        return

    print_banner()

    try:
        assert_git_repo()

        if pr:
            _handle_pr_command(locale, print_prompt)
            return

        if stage_all:
            run_git_command(["add", "-A"])
            
        cli_overrides = {}
        if locale:
            cli_overrides["locale"] = locale
        if generate:
            cli_overrides["generate"] = generate
        if type is not None:
            cli_overrides["type"] = type
        if exclude:
            cli_overrides["excludes"] = list(exclude)
            
        config = get_config(cli_overrides)
        
        diff = get_staged_diff(config_exclude=config.get("excludes", []))
        if not diff or not diff.files:
            console.print("[yellow]No staged files found. Please stage files using `git add` and try again.[/yellow]")
            sys.exit(0)
        
        file_count = len(diff.files)
        file_word = "file" if file_count == 1 else "files"
        console.print(f"[green]✓[/green] [bold]Detected {file_count} staged {file_word}:[/bold]")
        for f in diff.files:
            console.print(f"      {f}")
        console.print()
        branch_name = get_branch_name()
        services = get_available_services(config, diff, branch_name)
        
        if not services:
            console.print("[red]No AI providers configured. Please set an API key using `pycommit-ai config set PROVIDER.key=YOUR_KEY`.[/red]")
            console.print("Supported providers: GEMINI, OPENAI, GROQ, OPENROUTER")
            sys.exit(1)
            
        responses: List[Tuple[str, AIResponse]] = []
        
        with console.status("[bold green]Generating commit messages..."):
            for status, srv_name, result in generate_commits_parallel(services):
                if status == "success":
                    for r in result:
                        responses.append((srv_name, r))
                    console.print(f"[green]✓[/green] Generated from {srv_name}")
                else:
                    console.print(f"[red]✗[/red] Error from {srv_name}: {result}")
                        
        if not responses:
            console.print("[red]Failed to generate any commit messages.[/red]")
            sys.exit(1)
            
        if confirm:
            chosen_msg = responses[0][1].value
            chosen_title = responses[0][1].title
        else:
            choices = [
                Choice(
                    value=(item.title, item.value),
                    name=f"[{srv_name}] {item.title}"
                )
                for srv_name, item in responses
            ]
            
            chosen_title, chosen_msg = inquirer.select(
                message="Pick a commit message to use:",
                choices=choices,
                instruction="(Use arrow keys or type to search)",
                vi_mode=True,
            ).execute()
            
        if dry_run:
            console.print("\n[bold]Dry run — Selected Message:[/bold]")
            console.print(chosen_msg)
        elif copy:
            copy_to_clipboard(chosen_title)
            console.print(f"\n[bold green]Commit message copied to clipboard![/bold green]")
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
