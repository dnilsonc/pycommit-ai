#!/usr/bin/env python3
"""Bump the project version in pyproject.toml.

Usage:
    python bump_version.py patch   # 0.3.0 → 0.3.1
    python bump_version.py minor   # 0.3.0 → 0.4.0
    python bump_version.py major   # 0.3.0 → 1.0.0
"""

import re
import sys
from pathlib import Path

PYPROJECT = Path(__file__).parent / "pyproject.toml"
VERSION_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', re.MULTILINE)


def get_current_version(content: str) -> tuple[int, int, int]:
    match = VERSION_RE.search(content)
    if not match:
        print("❌ Could not find version in pyproject.toml")
        sys.exit(1)
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump(major: int, minor: int, patch: int, part: str) -> str:
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "major":
        return f"{major + 1}.0.0"
    else:
        print(f"❌ Unknown part '{part}'. Use: patch, minor, or major")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        part = "patch"
    else:
        part = sys.argv[1]

    content = PYPROJECT.read_text()
    major, minor, patch_v = get_current_version(content)
    old_version = f"{major}.{minor}.{patch_v}"
    new_version = bump(major, minor, patch_v, part)

    new_content = VERSION_RE.sub(f'version = "{new_version}"', content)
    PYPROJECT.write_text(new_content)

    print(f"✅ {old_version} → {new_version}")


if __name__ == "__main__":
    main()
