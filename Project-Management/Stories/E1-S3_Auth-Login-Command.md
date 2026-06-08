# Story: Auth Login Command

**Epic**: [E1 - Authentication & Setup](../Epics/E1_Authentication-Setup.md)
**Story ID**: E1-S3
**Story Points**: 3
**Priority**: High
**Status**: ✅ Done (automated) · ⏳ Manual verification pending

## User Story

As a **developer setting up the CLI for the first time**,
I want to **run `spotify-cli auth login` to open a browser and cache my tokens**,
So that **all subsequent commands run without prompting me to authenticate**.

## Description

Implement the `login` command in `auth/commands.py`. On first run it calls `require_client_id()`, then `get_auth_manager(open_browser=not no_browser).get_access_token(as_dict=False)`. spotipy handles browser launch, local callback server on `http://127.0.0.1:9090/callback`, PKCE challenge/verifier, token exchange, and writing the cache. On success, the command prints `{"status": "authenticated", "cache_path": "~/.config/spotify-cli/.cache"}` to stdout and exits 0.

The `--no-browser` flag passes `open_browser=False` to the factory — spotipy then prints the auth URL and accepts the redirect URL via stdin, enabling headless/SSH environments (SFR-06 / FR-09).

On subsequent runs with a cached refresh token, spotipy silently refreshes the access token — no code change needed; this is handled entirely by `CacheFileHandler` inside `get_auth_manager()`.

## Acceptance Criteria

- [ ] First run opens browser and captures redirect at `http://127.0.0.1:9090/callback` — **Manual verification pending** (live OAuth flow; see `Sprints/Sprint-02/manual-verification.md`)
- [ ] Token written to `~/.config/spotify-cli/.cache` with permissions 600 (enforced by spotipy ≥2.25.1) — **Manual verification pending**
- [ ] Subsequent runs within TTL do not open browser (silent refresh via spotipy) — **Manual verification pending** (Spotipy-owned behavior; TC-08 verifies `login()` delegates via `get_access_token(as_dict=False)`, but not the live refresh path)
- [x] `--no-browser` passes `open_browser=False` to factory (TC-03, automated) — Spotipy's URL-print/stdin-accept behavior is **manual verification pending**
- [x] Success output is valid JSON on stdout: `{"status": "authenticated", "cache_path": "~/.config/spotify-cli/.cache"}` — TC-01 (automated)
- [x] `SPOTIFY_CLIENT_ID` missing → exit 2 with structured JSON on stderr — TC-02 (automated; delegated to `require_client_id()`)
- [x] TC-01 and TC-03 from SPEC-001 §2.6 pass via `uv run pytest` (automated)

## Technical Notes

### Implementation Approach

1. Implement `login(no_browser: bool)` command in `auth/commands.py` with `typer.Option` for `--no-browser`
2. Call `require_client_id()` first (exits 2 if env var missing)
3. Call `get_auth_manager(open_browser=not no_browser).get_access_token(as_dict=False)` — spotipy handles everything
4. On success, `typer.echo(json.dumps({"status": "authenticated", "cache_path": str(CACHE_PATH)}))` and `raise typer.Exit(code=0)`
5. Add TC-01 (mock success, assert JSON + exit 0) and TC-03 (`--no-browser`, assert `open_browser=False` passed) to `tests/auth/test_auth_commands.py`

### Code Examples (if helpful)

```python
# auth/commands.py — login
import json
import typer
from spotify_cli.core.spotify_client import get_auth_manager, require_client_id, CACHE_PATH


def login(
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Print auth URL to stdout and accept redirect URL via stdin (headless/SSH).",
    )
) -> None:
    """
    Authenticate with Spotify via OAuth 2.0 PKCE.

    Usage: spotify-cli auth login [--no-browser]
    Example: spotify-cli auth login
    Example: spotify-cli auth login --no-browser
    """
    require_client_id()
    auth_manager = get_auth_manager(open_browser=not no_browser)
    auth_manager.get_access_token(as_dict=False)
    typer.echo(json.dumps({"status": "authenticated", "cache_path": str(CACHE_PATH)}))
    raise typer.Exit(code=0)
```

```python
# tests/auth/test_auth_commands.py — TC-01 and TC-03
def test_login_success():
    """TC-01: auth login with SPOTIFY_CLIENT_ID set opens browser and exits 0."""
    mock_manager = MagicMock()
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    assert json.loads(result.output)["status"] == "authenticated"


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
```

### Files/Components Affected

- `spotify_cli/auth/commands.py` — implements `login()` (fills in stub from E1-S1)
- `tests/auth/test_auth_commands.py` — TC-01 and TC-03 added

### External Dependencies

- `spotipy>=2.25.1` — `SpotifyPKCE.get_access_token()`, browser launch, callback server, cache write
- `typer` — `typer.Option`, `typer.echo`, `typer.Exit`
- `SPOTIFY_CLIENT_ID` env var — required; validated by `require_client_id()` from E1-S2
- `http://127.0.0.1:9090/callback` — must be registered in Spotify developer dashboard

## Definition of Done

- [x] Code implemented and follows conventions
- [~] All acceptance criteria met — automated portion complete; manual portion pending (see AC above)
- [x] TC-01 and TC-03 written and passing via `uv run pytest`
- [ ] Manual test: `uv run spotify-cli auth login` opens browser and writes cache — **pending live OAuth run**
- [ ] Manual test: `stat -f "%A" ~/.config/spotify-cli/.cache` shows `600` — **pending live OAuth run**
- [x] Self-reviewed
- [x] No known bugs or issues

## Dependencies

**Depends On**:
- E1-S1: Project Scaffold — `main.py` entry point and package structure
- E1-S2: Spotify Client Factory — `require_client_id()`, `get_auth_manager()`, `CACHE_PATH`

**Blocks**:
- E1-S4: Auth Status & Logout + Tests — login must work before status/logout are meaningful to test end-to-end

## Related Stories

- E1-S2: Spotify Client Factory — this story is the primary consumer of the factory
- E1-S4: Auth Status & Logout + Tests — shares `auth/commands.py`; TC-08 (silent refresh) is verified here

## Notes

- The cache JSON output includes `cache_path` for transparency — useful for scripts and debugging
- TC-08 (silent refresh) is a behaviour of spotipy, not an explicit code path — it is verified via manual test after login
- SPEC-001 §3.2 (T-07, T-09) and §3.3 (T-12) map to the tasks in this story
- The `as_dict=False` argument to `get_access_token()` suppresses the return value and avoids parsing overhead

---

**Created**: 2026-06-04
**Completed**: 2026-06-08
**Status**: ✅ Done
