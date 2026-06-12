import json
import time
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from spotify_cli.main import app
from spotify_cli.core.spotify_client import get_auth_manager, get_cached_token

runner = CliRunner()


@pytest.fixture(autouse=True)
def set_client_id(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "test-client-secret")


# TC-01: login success
def test_login_success():
    """TC-01: auth login with SPOTIFY_CLIENT_ID set exits 0 with authenticated JSON."""
    mock_manager = MagicMock()
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    assert json.loads(result.output)["status"] == "authenticated"


# TC-02: login missing SPOTIFY_CLIENT_ID → exit 2
def test_login_missing_client_id(monkeypatch):
    """TC-02: require_client_id() with SPOTIFY_CLIENT_ID unset exits 2 with JSON."""
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 2
    parsed = json.loads(result.output)
    assert parsed["error"] == "SPOTIFY_CLIENT_ID not set"
    assert "reason" in parsed
    assert "suggestion" in parsed
    assert "help" in parsed


# TC-03: --no-browser passes open_browser=False
def test_login_no_browser():
    """TC-03: --no-browser passes open_browser=False to SpotifyPKCE factory."""
    mock_manager = MagicMock()
    with patch(
        "spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager
    ) as mock_pkce:
        result = runner.invoke(app, ["auth", "login", "--no-browser"])
    assert result.exit_code == 0
    _, kwargs = mock_pkce.call_args
    assert kwargs.get("open_browser") is False


# TC-04: status with valid token
def test_status_valid_token():
    """TC-04: auth status with valid cached token returns status=valid and scopes."""
    mock_token = {
        "access_token": "tok",
        "expires_at": time.time() + 3600,
        "scope": "playlist-modify-public user-read-private",
    }
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path, \
         patch("spotify_cli.auth.commands.get_cached_token", return_value=mock_token):
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["status"] == "valid"
    assert parsed["expires_in_seconds"] > 0
    assert parsed["scopes"] == ["playlist-modify-public", "user-read-private"]


# TC-05: status with no cache file
def test_status_missing_cache():
    """TC-05: auth status with no cache file returns status=missing."""
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "missing"}


# TC-05a: status with expired cached token
def test_status_expired_token():
    """status returns expired with negative expires_in_seconds when token has past expiry."""
    mock_token = {
        "access_token": "old",
        "expires_at": time.time() - 120,
        "scope": "playlist-modify-public",
    }
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path, \
         patch("spotify_cli.auth.commands.get_cached_token", return_value=mock_token):
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["status"] == "expired"
    assert parsed["expires_in_seconds"] < 0
    assert "scopes" not in parsed


# TC-05b: status with cache file present but get_cached_token returns None
def test_status_cached_token_none():
    """status returns missing when cache file exists but get_cached_token returns None."""
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path, \
         patch("spotify_cli.auth.commands.get_cached_token", return_value=None):
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "missing"}


# TC-05c: status with cache file present but SPOTIFY_CLIENT_ID unset
def test_status_with_cache_no_client_id(monkeypatch):
    """status inspects cached token without requiring SPOTIFY_CLIENT_ID."""
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    mock_token = {
        "access_token": "tok",
        "expires_at": time.time() + 3600,
        "scope": "playlist-modify-public",
    }
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path, \
         patch("spotify_cli.auth.commands.get_cached_token", return_value=mock_token):
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["status"] == "valid"
    assert parsed["expires_in_seconds"] > 0


# TC-06: logout with cache present
def test_logout_with_cache():
    """TC-06: auth logout with cache present deletes file and returns logged_out."""
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    mock_path.unlink.assert_called_once()
    assert json.loads(result.output) == {"status": "logged_out"}


# TC-07: logout without cache
def test_logout_no_cache():
    """TC-07: auth logout with no cache returns no_session gracefully (idempotent)."""
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "no_session"}


# TC-08 (reworked): login() delegates to SpotifyPKCE.get_access_token(as_dict=False).
# True silent-refresh behavior is owned by Spotipy and verified via documented manual
# integration (see Project-Management/Sprints/Sprint-02/manual-verification.md).
def test_login_invokes_get_access_token_as_dict_false():
    """login() must call SpotifyPKCE.get_access_token(as_dict=False) — the contract
    that lets Spotipy decide whether to use the cached token or refresh silently.
    """
    mock_manager = MagicMock()
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    mock_manager.get_access_token.assert_called_once_with(as_dict=False)


# Factory unit tests (kept from Sprint-01)
def test_get_auth_manager_creates_cache_directory(tmp_path, monkeypatch):
    """get_auth_manager() must ensure the cache directory exists."""
    monkeypatch.setattr("spotify_cli.core.spotify_client.CACHE_PATH", tmp_path / ".config" / "spotify-cli" / ".cache")
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE"):
        get_auth_manager()
    assert (tmp_path / ".config" / "spotify-cli").exists()


def test_get_auth_manager_passes_open_browser_false(tmp_path, monkeypatch):
    """get_auth_manager(open_browser=False) passes the flag through to SpotifyPKCE."""
    monkeypatch.setattr("spotify_cli.core.spotify_client.CACHE_PATH", tmp_path / ".cache")
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE") as mock_pkce:
        get_auth_manager(open_browser=False)
    call_kwargs = mock_pkce.call_args.kwargs
    assert call_kwargs.get("open_browser") is False


def test_get_cached_token_reads_from_cache_path(tmp_path, monkeypatch):
    """get_cached_token() uses CacheFileHandler bound to CACHE_PATH (no SpotifyPKCE)."""
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    cache_file = tmp_path / ".cache"
    monkeypatch.setattr("spotify_cli.core.spotify_client.CACHE_PATH", cache_file)
    sentinel_token = {"access_token": "x", "expires_at": 0, "scope": ""}
    with patch(
        "spotify_cli.core.spotify_client.spotipy.cache_handler.CacheFileHandler"
    ) as mock_handler_cls:
        mock_handler_cls.return_value.get_cached_token.return_value = sentinel_token
        result = get_cached_token()
    mock_handler_cls.assert_called_once_with(cache_path=str(cache_file))
    assert result is sentinel_token
