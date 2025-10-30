"""Pytest configuration and fixtures."""

import pytest
from pytest_asyncio import is_async_test


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("asyncio_mode", "auto")

