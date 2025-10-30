"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path for tests
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def pytest_configure(config):
    """Configure pytest markers."""
    # asyncio_mode is configured in pyproject.toml
    pass

