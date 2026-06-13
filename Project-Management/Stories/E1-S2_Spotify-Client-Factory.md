# Story: Spotify Client Factory

**Epic**: [E1 - Authentication & Setup](../Epics/E1_Authentication-Setup.md)
**Story ID**: E1-S2
**Story Points**: 2
**Priority**: High
**Status**: ✅ Done

## User Story

As a **developer**,
I want to **have a shared `spotify_client.py` factory that creates an authenticated SpotifyPKCE instance**,
So that **all commands share the same auth logic and cache path without duplication**.

## Description

Implement `core/spotify_client.py` as the single source of truth for the authentication manager. It defines `CACHE_PATH`, `SCOPES`, `REDIRECT_URI`, and two public functions: `get_auth_manager(open_browser)` which constructs and returns a `SpotifyPKCE` instance with `CacheFileHandler`, and `require_client_id()` which guards against a missing `SPOTIFY_CLIENT_ID` env var by writing a structured JSON error to stderr and raising `typer.Exit(code=2)`. The factory also ensures the cache directory exists on every call.

No browser interaction or token exchange happens in this story — that is E1-S3. This story only establishes the shared factory and guard that E1-S3 and E1-S4 depend on.

## Acceptance Criteria

- [ ] `SPOTIFY_CLIENT_ID` unset → exits 2 with structured JSON on stderr containing `"error"`, `"reason"`, `"suggestion"`, and `"help"` keys
- [ ] `CACHE_PATH` resolves to `~/.config/spotify-cli/.cache`
- [ ] Cache directory (`~/.config/spotify-cli/`) is created automatically via `mkdir(parents=True, exist_ok=True)` if missing
- [ ] `get_auth_manager(open_browser=False)` passes `open_browser=False` through to `SpotifyPKCE` constructor
- [ ] Unit test: missing env var produces exit code 2 and correct JSON shape (TC-02)

## Technical Notes

### Implementation Approach

1. Implement `CACHE_PATH = pathlib.Path.home() / ".config" / "spotify-cli" / ".cache"` as a module-level constant
2. Implement `require_client_id()`: check `os.environ.get("SPOTIFY_CLIENT_ID")`; if missing, write structured JSON to stderr via `typer.echo(..., err=True)` and raise `typer.Exit(code=2)`
3. Implement `get_auth_manager(open_browser=True)`: call `CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)`, then construct and return `SpotifyPKCE` with all required kwargs
4. Write unit test for TC-02 in `tests/auth/test_auth_commands.py` — mock env var absence, assert exit code and JSON shape

### Code Examples (if helpful)

```python
# spotify_cli/core/spotify_client.py
import os
import pathlib
import typer
import spotipy
from spotipy.oauth2 import SpotifyPKCE

CACHE_PATH = pathlib.Path.home() / ".config" / "spotify-cli" / ".cache"
SCOPES = "playlist-modify-public playlist-modify-private user-read-private"
REDIRECT_URI = "http://127.0.0.1:9090/callback"


def require_client_id() -> None:
    if not os.environ.get("SPOTIFY_CLIENT_ID"):
        typer.echo(
            '{"error": "SPOTIFY_CLIENT_ID not set", '
            '"reason": "Required env var missing", '
            '"suggestion": "export SPOTIFY_CLIENT_ID=your_client_id", '
            '"help": "spotify-cli auth --help"}',
            err=True,
        )
        raise typer.Exit(code=2)


def get_auth_manager(open_browser: bool = True) -> SpotifyPKCE:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SpotifyPKCE(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_handler=spotipy.cache_handler.CacheFileHandler(
            cache_path=str(CACHE_PATH)
        ),
        open_browser=open_browser,
    )
```

### Files/Components Affected

- `spotify_cli/core/spotify_client.py` — implements the stub created in E1-S1
- `tests/auth/test_auth_commands.py` — TC-02 unit test added here

### External Dependencies

- `spotipy>=2.25.1` — `SpotifyPKCE`, `CacheFileHandler`; 600-permission enforcement via CVE-2025-27154 fix
- `typer` — `typer.Exit`, `typer.echo`

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] TC-02 test written and passing via `uv run pytest`
- [ ] Self-reviewed
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E1-S1: Project Scaffold — package structure and stubs must exist

**Blocks**:
- E1-S3: Auth Login Command — calls `require_client_id()` and `get_auth_manager()`
- E1-S4: Auth Status & Logout + Tests — imports `CACHE_PATH` and `get_auth_manager()`

## Related Stories

- E1-S1: Project Scaffold — creates the package skeleton this story fills in
- E1-S3: Auth Login Command — primary consumer of `get_auth_manager()`
- E1-S4: Auth Status & Logout + Tests — secondary consumer of `CACHE_PATH` and `get_auth_manager()`

## Notes

- > **Conflict note**: SPEC-001 §1.10 lists `SPOTIFY_CLIENT_SECRET` in the Dependencies table, and a prior note in this file stated it was required. ADR-001 (Authentication Flow — PKCE) is authoritative: PKCE requires no client secret. Sprint-01 follows ADR-001. Only `SPOTIFY_CLIENT_ID` is needed.
- The JSON error on stderr uses `typer.echo(..., err=True)` — Typer `CliRunner` merges stderr into `.output` by default; keep this in mind when writing TC-02
- SPEC-001 §3.2 (T-05, T-06, T-08) maps directly to the tasks in this story
- Phase 2 of SPEC-001 maps this as the foundation before `auth login` (T-07)

---

**Created**: 2026-06-04
**Status**: ✅ Done — 2026-06-05
