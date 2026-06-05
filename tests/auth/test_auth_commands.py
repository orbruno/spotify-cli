import json
import os
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from spotify_cli.main import app
from spotify_cli.core.spotify_client import get_auth_manager

runner = CliRunner()


def test_login_missing_client_id(monkeypatch):
    """TC-02: require_client_id() with SPOTIFY_CLIENT_ID unset exits 2 with JSON on stderr."""
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 2
    # Typer CliRunner merges stderr into .output by default
    parsed = json.loads(result.output)
    assert parsed["error"] == "SPOTIFY_CLIENT_ID not set"
    assert "reason" in parsed
    assert "suggestion" in parsed
    assert "help" in parsed


def test_get_auth_manager_creates_cache_directory(tmp_path, monkeypatch):
    """get_auth_manager() must ensure the cache directory exists."""
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-id")
    monkeypatch.setattr("spotify_cli.core.spotify_client.CACHE_PATH", tmp_path / ".config" / "spotify-cli" / ".cache")
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE"):
        get_auth_manager()
    assert (tmp_path / ".config" / "spotify-cli").exists()


def test_get_auth_manager_passes_open_browser_false(tmp_path, monkeypatch):
    """get_auth_manager(open_browser=False) passes the flag through to SpotifyPKCE."""
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-id")
    monkeypatch.setattr("spotify_cli.core.spotify_client.CACHE_PATH", tmp_path / ".cache")
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE") as mock_pkce:
        get_auth_manager(open_browser=False)
    call_kwargs = mock_pkce.call_args.kwargs
    assert call_kwargs.get("open_browser") is False
