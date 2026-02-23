import subprocess
from dataclasses import dataclass
from typing import List, Optional

from pycommit_ai.errors import KnownError


@dataclass
class GitDiff:
    files: List[str]
    diff: str


def run_git_command(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the completed process."""
    try:
        return subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=check,
        )
    except subprocess.CalledProcessError as e:
        if check:
            raise e
        return e


def assert_git_repo() -> str:
    """Assert that the current directory is a git repository and return its top level."""
    result = run_git_command(["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        raise KnownError("The current directory must be a Git repository!")
    return result.stdout.strip()


def get_branch_name() -> str:
    """Get the current git branch name."""
    result = run_git_command(["branch", "--show-current"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def _exclude_from_diff(path: str) -> str:
    return f":(exclude){path}"


FILES_TO_EXCLUDE = [
    _exclude_from_diff(f)
    for f in [
        "package-lock.json",
        "pnpm-lock.yaml",
        "*.lock",
        "*.lockb",
        "uv.lock",
        "poetry.lock",
    ]
]


def get_staged_diff(exclude_files: Optional[List[str]] = None, config_exclude: Optional[List[str]] = None) -> Optional[GitDiff]:
    """Get the staged git diff."""
    exclude_files = exclude_files or []
    config_exclude = config_exclude or []

    exclude_args = FILES_TO_EXCLUDE + [
        _exclude_from_diff(f) for f in exclude_files
    ] + [
        _exclude_from_diff(f) for f in config_exclude
    ]

    diff_cached_base = ["diff", "--cached", "--diff-algorithm=minimal"]

    # Get the file names
    files_result = run_git_command(diff_cached_base + ["--name-only"] + exclude_args, check=False)
    if files_result.returncode != 0 or not files_result.stdout.strip():
        return None

    files = [f for f in files_result.stdout.strip().split("\n") if f]
    
    if not files:
        return None

    # Get the diff content
    diff_result = run_git_command(diff_cached_base + exclude_args, check=True)
    diff = diff_result.stdout

    # Get binary files using numstat
    numstat_result = run_git_command(diff_cached_base + ["--numstat"] + exclude_args, check=True)
    binary_files = []
    
    for line in numstat_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0] == "-" and parts[1] == "-":
            binary_files.append(parts[2])

    enhanced_diff = diff
    if binary_files:
        if not diff.strip():
            enhanced_diff = ""
        enhanced_diff += "\n\n--- Binary Files Changed ---\n"
        for file in binary_files:
            # We can use git status to get the action but let's just say it changed for simplicity
            enhanced_diff += f"Binary file {file} changed\n"

    all_staged_files = list(set(files + binary_files))

    if not enhanced_diff:
        enhanced_diff = f"Files changed: {', '.join(all_staged_files)}"

    return GitDiff(files=all_staged_files, diff=enhanced_diff)


def commit_changes(message: str, raw_argv: List[str] = None):
    """Commit changes with the given message."""
    try:
        run_git_command(["commit", "-m", message], check=True)
    except subprocess.CalledProcessError as e:
        raise KnownError(f"Failed to commit changes: {e.stderr}")


def get_merge_base(target_branch: str = "main") -> str:
    """Find the merge base between the current branch and the target branch."""
    # Try main first, then master
    for branch in [target_branch, "main", "master"]:
        result = run_git_command(["merge-base", "HEAD", branch], check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    raise KnownError("Could not find merge base. Make sure 'main' or 'master' branch exists.")


def get_merge_base_diff(target_branch: str = "main") -> GitDiff:
    """Get the diff between the current branch HEAD and the merge base."""
    base = get_merge_base(target_branch)

    # Get changed file names
    files_result = run_git_command(["diff", "--name-only", base, "HEAD"] + FILES_TO_EXCLUDE, check=False)
    files = [f for f in files_result.stdout.strip().split("\n") if f] if files_result.stdout.strip() else []

    if not files:
        raise KnownError("No changes found between current branch and base branch.")

    # Get the diff
    diff_result = run_git_command(["diff", "--diff-algorithm=minimal", base, "HEAD"] + FILES_TO_EXCLUDE, check=True)

    return GitDiff(files=files, diff=diff_result.stdout)


def get_branch_commits(target_branch: str = "main") -> List[str]:
    """Get the list of commit messages between the merge base and HEAD."""
    base = get_merge_base(target_branch)
    result = run_git_command(["log", "--pretty=format:%s", f"{base}..HEAD"], check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [line for line in result.stdout.strip().split("\n") if line]
