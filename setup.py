#!/usr/bin/env python
"""Minimal setup.py for editable installs with older pip versions.

The canonical project metadata lives in pyproject.toml (managed by Poetry).
This file exists solely to support `pip install -e .` on pip < 21.3, which
does not support PEP 660 editable installs from pyproject.toml alone.

Recommended: upgrade pip first — `pip install --upgrade pip`
Then use:    `pip install -e .`  or  `poetry install`
"""

from setuptools import find_packages, setup

setup(
    name="costpulse",
    version="0.2.0",
    packages=find_packages(exclude=["tests*", "frontend*", "docs*", "alembic*"]),
    python_requires=">=3.10",
    install_requires=[
        "databricks-sdk>=0.20.0",
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.29.0",
        "alembic>=1.13.0",
        "redis>=5.0.0",
        "click>=8.1.0",
        "rich>=13.7.0",
        "httpx>=0.26.0",
        "python-dotenv>=1.0.0",
        "structlog>=24.1.0",
        "numpy>=1.26.0",
    ],
    entry_points={
        "console_scripts": [
            "costpulse=costpulse.cli.main:cli",
        ],
    },
)
