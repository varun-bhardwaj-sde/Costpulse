#!/usr/bin/env python
"""Minimal setup.py for editable installs with older pip versions.

The canonical project metadata lives in pyproject.toml (managed by Poetry).
This file exists solely to support `pip install -e .` on pip < 21.3, which
does not support PEP 660 editable installs from pyproject.toml alone.

Version and dependencies are parsed from pyproject.toml at build time so
there is a single source of truth.

Recommended: upgrade pip first — `pip install --upgrade pip`
Then use:    `pip install -e .`  or  `poetry install`
"""

import re
from pathlib import Path

from setuptools import find_packages, setup

_PYPROJECT = Path(__file__).parent / "pyproject.toml"


def _read_pyproject() -> str:
    return _PYPROJECT.read_text(encoding="utf-8")


def _parse_version(text: str) -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not parse version from pyproject.toml")
    return match.group(1)


def _parse_dependencies(text: str) -> list:
    """Extract non-optional dependencies from [tool.poetry.dependencies]."""
    deps = []
    in_deps = False
    for line in text.splitlines():
        if line.strip() == "[tool.poetry.dependencies]":
            in_deps = True
            continue
        if in_deps and line.strip().startswith("["):
            break
        if not in_deps:
            continue

        # Skip python constraint and blank/comment lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Skip the python version constraint (but not python-dotenv etc.)
        if re.match(r"^python\s*=", stripped):
            continue

        # Simple: package = ">=1.0.0"
        simple = re.match(r'^(\S+)\s*=\s*"([^"]+)"', stripped)
        if simple:
            deps.append(f"{simple.group(1)}{simple.group(2)}")
            continue

        # Table-inline with version: package = {version = ">=1.0", ...}
        # Skip entries marked optional = true
        if "optional = true" in stripped.lower():
            continue
        table = re.match(r'^(\S+)\s*=\s*\{.*version\s*=\s*"([^"]+)"', stripped)
        if table:
            # Handle extras: {extras = ["standard"], version = ">=0.27.0"}
            extras_match = re.search(r'extras\s*=\s*\["([^"]+)"\]', stripped)
            if extras_match:
                deps.append(f"{table.group(1)}[{extras_match.group(1)}]{table.group(2)}")
            else:
                deps.append(f"{table.group(1)}{table.group(2)}")

    return deps


_text = _read_pyproject()

setup(
    name="costpulse",
    version=_parse_version(_text),
    packages=find_packages(exclude=["tests*", "frontend*", "docs*", "alembic*"]),
    python_requires=">=3.10",
    install_requires=_parse_dependencies(_text),
    entry_points={
        "console_scripts": [
            "costpulse=costpulse.cli.main:cli",
        ],
    },
)
