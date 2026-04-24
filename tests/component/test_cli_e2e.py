"""Component/integration tests for ha_shopping_list CLI."""

from __future__ import annotations

import re
import subprocess
import sys

import pytest


@pytest.mark.component
def test_cli_entrypoint() -> None:
    """Test CLI entry point via console script."""
    result = subprocess.run(
        ["ha_shopping_list", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "A better shopping list for homeassistant" in result.stdout or "usage:" in result.stdout


@pytest.mark.component
def test_cli_module_invocation() -> None:
    """Test CLI via python -m invocation."""
    result = subprocess.run(
        [sys.executable, "-m", "ha_shopping_list", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "A better shopping list for homeassistant" in result.stdout or "usage:" in result.stdout


@pytest.mark.component
def test_cli_version() -> None:
    """Test CLI --version flag."""
    result = subprocess.run(
        ["ha_shopping_list", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert re.search(r"\d+\.\d+", result.stdout), f"No version in output: {result.stdout!r}"
