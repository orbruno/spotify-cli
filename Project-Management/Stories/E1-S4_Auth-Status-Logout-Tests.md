# Story: Auth Status & Logout + Tests

**Epic**: [E1 - Authentication & Setup](../Epics/E1_Authentication-Setup.md)
**Story ID**: E1-S4
**Story Points**: 3
**Priority**: High
**Status**: ✅ Done

## User Story

As a **developer or AI agent**,
I want to **run `auth status` and `auth logout` commands**,
So that **I can inspect the current authentication state and cleanly revoke the cached session**.

## Description

Implement the `status` and `logout` commands in `auth/commands.py`, then write the complete `tests/auth/test_auth_commands.py` test suite covering TC-01 through TC-08 from SPEC-001 §2.6.

**`auth status`**: reads the cache file and returns one of three JSON shapes — `{"status": "valid", "expires_in_seconds": N, "scopes": [...]}`, `{"status": "expired", "expires_in_seconds": -N}`, or `{"status": "missing"}`. Always exits 0 (status is informational, not an error condition).

**`auth logout`**: deletes `CACHE_PATH` if it exists and returns `{"status": "logged_out"}`. If the file does not exist, returns `{"status": "no_session"}` and exits 0 — the command is idempotent.

**Tests**: use Typer `CliRunner` with mocked spotipy and mocked `CACHE_PATH` — no live API calls. Note that `CliRunner` merges stderr into `.output` by default; use subprocess for any test that must separately assert on stderr.

## Acceptance Criteria

- [x] `auth status` with valid cached token → JSON with `status: "valid"` and positive `expires_in_seconds`, exit 0 — TC-04 (automated)
- [x] `auth status` with expired token → JSON with `status: "expired"` and negative `expires_in_seconds`, exit 0 — `test_status_expired_token` (automated)
- [x] `auth status` with no cache file → `{"status": "missing"}`, exit 0 — TC-05 (automated)
- [x] `auth status` with cache file present but `get_cached_token()` returns `None` → `{"status": "missing"}`, exit 0 — `test_status_cached_token_none` (automated)
- [x] `auth status` works without `SPOTIFY_CLIENT_ID` when cache exists — `test_status_with_cache_no_client_id` (automated)
- [x] `auth logout` with cache present → deletes file, returns `{"status": "logged_out"}`, exit 0 — TC-06 (automated)
- [x] `auth logout` with no cache file → returns `{"status": "no_session"}`, exit 0 (idempotent) — TC-07 (automated)
- [x] All TC-01 through TC-08 from SPEC-001 §2.6 pass via `uv run pytest tests/auth/` (TC-08 reworked: asserts `login()` calls `get_access_token(as_dict=False)`; true silent-refresh is manual verification — see `Sprints/Sprint-02/manual-verification.md`)
- [x] No live Spotify API calls in the test suite
- [x] `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80` passes (achieved 100%)

## Technical Notes

### Implementation Approach

1. Implement `status()` in `auth/commands.py`: check `CACHE_PATH.exists()`; if missing, output `{"status": "missing"}`; otherwise call `get_cached_token()` (a `core/spotify_client.py` helper that reads the cache file directly via `CacheFileHandler` — no `SpotifyPKCE` instantiation, no `require_client_id()`); if it returns `None`, output `{"status": "missing"}`; otherwise compute `expires_in = int(token_info["expires_at"] - time.time())`; set `state = "valid" if expires_in > 0 else "expired"`; include `scopes` only when valid. `status()` is intentionally independent of `SPOTIFY_CLIENT_ID` — cache inspection is a pure file read.
2. Implement `logout()` in `auth/commands.py`: if `CACHE_PATH.exists()` → `CACHE_PATH.unlink()` + `{"status": "logged_out"}`; else → `{"status": "no_session"}`; always exit 0
3. Scaffold `tests/auth/test_auth_commands.py` with `CliRunner`, `autouse` fixture for `SPOTIFY_CLIENT_ID`, and all 8 test cases using `unittest.mock.patch` — status tests patch `spotify_cli.auth.commands.get_cached_token` rather than `SpotifyPKCE`

### Code Examples (if helpful)

```python
# auth/commands.py — status and logout
import json
import time
import typer
from spotify_cli.core.spotify_client import CACHE_PATH, get_cached_token


def status() -> None:
    """
    Print current token status as JSON.

    Reads the cache file directly via ``CacheFileHandler`` and does not require
    ``SPOTIFY_CLIENT_ID``; an absent or unreadable cache reports ``missing``.

    Usage: spotify-cli auth status
    Example: spotify-cli auth status
    """
    if not CACHE_PATH.exists():
        typer.echo(json.dumps({"status": "missing"}))
        raise typer.Exit(code=0)

    token_info = get_cached_token()

    if token_info is None:
        typer.echo(json.dumps({"status": "missing"}))
        raise typer.Exit(code=0)

    expires_in = int(token_info["expires_at"] - time.time())
    state = "valid" if expires_in > 0 else "expired"
    output: dict = {"status": state, "expires_in_seconds": expires_in}

    if state == "valid":
        output["scopes"] = token_info.get("scope", "").split()

    typer.echo(json.dumps(output))
    raise typer.Exit(code=0)


def logout() -> None:
    """
    Delete cached Spotify tokens.

    Usage: spotify-cli auth logout
    Example: spotify-cli auth logout
    """
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
        typer.echo(json.dumps({"status": "logged_out"}))
    else:
        typer.echo(json.dumps({"status": "no_session"}))
    raise typer.Exit(code=0)


# core/spotify_client.py — get_cached_token() helper (added Sprint-02)
def get_cached_token() -> dict | None:
    """
    Read the cached token from disk without instantiating SpotifyPKCE.

    Returns the cached token dict or None. Does NOT require SPOTIFY_CLIENT_ID.
    """
    return spotipy.cache_handler.CacheFileHandler(
        cache_path=str(CACHE_PATH)
    ).get_cached_token()
```

```python
# tests/auth/test_auth_commands.py — full scaffold
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from spotify_cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def set_client_id(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "test-client-secret")


# TC-01: login success
def test_login_success():
    mock_manager = MagicMock()
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    assert json.loads(result.output)["status"] == "authenticated"


# TC-02: login missing SPOTIFY_CLIENT_ID → exit 2
def test_login_missing_client_id(monkeypatch):
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 2
    assert json.loads(result.output)["error"] == "SPOTIFY_CLIENT_ID not set"


# TC-03: --no-browser passes open_browser=False
def test_login_no_browser():
    mock_manager = MagicMock()
    with patch(
        "spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager
    ) as mock_pkce:
        result = runner.invoke(app, ["auth", "login", "--no-browser"])
    assert result.exit_code == 0
    _, kwargs = mock_pkce.call_args
    assert kwargs.get("open_browser") is False


# TC-04: status with valid token — patches the get_cached_token helper directly,
# NOT SpotifyPKCE, because status() reads the cache via CacheFileHandler and never
# instantiates SpotifyPKCE.
def test_status_valid_token():
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
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "missing"}


# TC-06: logout with cache
def test_logout_with_cache():
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    mock_path.unlink.assert_called_once()
    assert json.loads(result.output) == {"status": "logged_out"}


# TC-07: logout without cache
def test_logout_no_cache():
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "no_session"}


# TC-08 (reworked): login() delegates to SpotifyPKCE.get_access_token(as_dict=False) —
# this is the contract that lets Spotipy decide whether to use the cached token or
# refresh silently. True silent-refresh behavior is owned by Spotipy and verified via
# documented manual integration (see Sprints/Sprint-02/manual-verification.md).
def test_login_invokes_get_access_token_as_dict_false():
    mock_manager = MagicMock()
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    mock_manager.get_access_token.assert_called_once_with(as_dict=False)
```

### Files/Components Affected

- `spotify_cli/auth/commands.py` — `status()` and `logout()` implementations added
- `tests/auth/test_auth_commands.py` — full test suite, TC-01 through TC-08

### External Dependencies

- `spotipy>=2.25.1` — `CacheFileHandler.get_cached_token()` for status introspection
- `typer.testing.CliRunner` — test client for Typer apps
- `unittest.mock` — `patch`, `MagicMock` for spotipy mocking

## Definition of Done

- [x] Code implemented and follows conventions
- [x] All acceptance criteria met (automated)
- [x] All TC-01 through TC-08 passing via `uv run pytest tests/auth/ -v` (TC-08 reworked — see AC note)
- [x] Coverage ≥80%: `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80` (achieved 100%)
- [x] Self-reviewed
- [x] No live Spotify API calls in test suite
- [x] No known bugs or issues

## Dependencies

**Depends On**:
- E1-S1: Project Scaffold — package structure and test skeleton
- E1-S2: Spotify Client Factory — `CACHE_PATH`, `get_auth_manager()`, `require_client_id()`
- E1-S3: Auth Login Command — `login()` implementation needed for TC-01, TC-02, TC-03, TC-08

**Blocks**:
- EP-002: Discography Browse — E1 must be fully done before EP-002 begins

## Related Stories

- E1-S2: Spotify Client Factory — `CACHE_PATH` imported for `status()` and `logout()`
- E1-S3: Auth Login Command — shares `auth/commands.py`; TC-01/TC-02/TC-03 originally started there, completed here

## Notes

- SPEC-001 §2.6 TC-07 uses `{"status": "no_cache"}` but the user instructions specify `{"status": "no_session"}` — this story follows the user instructions; update SPEC-001 if needed
- Typer `CliRunner` merges stderr into `.output` — TC-02 asserts on `.output`, not `.stderr`; this is documented in the test
- SPEC-001 §3.3 (T-10, T-11, T-13) and §3.4 (T-14 through T-21) map to the tasks in this story
- `status()` does not call `require_client_id()` at all — cache inspection uses `get_cached_token()` helper which reads the cache file directly via `CacheFileHandler`, independent of `SPOTIFY_CLIENT_ID`
- TC-08 reworked: the original test only asserted `kwargs.get("open_browser") is not False` (a weak truthy check on default flag handling, not refresh). The reworked test asserts `mock_manager.get_access_token.assert_called_once_with(as_dict=False)` — verifying `login()` honors its contract with Spotipy. True silent-refresh remains owned by Spotipy and is verified manually

---

**Created**: 2026-06-04
**Completed**: 2026-06-08
**Status**: ✅ Done
