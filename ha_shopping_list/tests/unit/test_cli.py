"""Unit tests for ha_shopping_list.cli."""

from __future__ import annotations

from unittest.mock import patch

from ha_shopping_list.cli import main


def test_main_no_args_starts_server() -> None:
    """main() with no extra args should call uvicorn.run and return 0."""
    with patch("uvicorn.run") as mock_run:
        result = main([])
    mock_run.assert_called_once()
    assert result == 0


def test_main_passes_host_and_port(monkeypatch) -> None:
    """CLI --host / --port flags are forwarded to uvicorn."""
    import ha_shopping_list.settings as settings_mod

    # Reset the singleton so Settings re-reads our env overrides.
    monkeypatch.setattr(settings_mod, "_settings", None)
    with patch("uvicorn.run") as mock_run:
        result = main(["--host", "127.0.0.1", "--port", "9000"])
    assert result == 0
    _, kwargs = mock_run.call_args
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 9000


def test_main_passes_api_key(monkeypatch) -> None:
    """CLI --api-key flag is forwarded to Settings (and thus the API key middleware)."""
    import ha_shopping_list.settings as settings_mod

    monkeypatch.setattr(settings_mod, "_settings", None)
    with patch("uvicorn.run"):
        result = main(["--api-key", "s3cret"])
    assert result == 0
    assert settings_mod.get_settings().api_key == "s3cret"


def test_main_help() -> None:
    """--help exits with code 0."""
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0


def test_main_version() -> None:
    """--version exits with code 0."""
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
