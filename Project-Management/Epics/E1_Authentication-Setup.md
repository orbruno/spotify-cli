# Epic 1: Authentication & Setup

**Epic ID**: E1
**Status**: To Do
**Priority**: High
**Story Points**: 10 points
**Owner**: Orlando Bruno

## Epic Description

As a **developer and end user**,
I need to **scaffold the Python project and implement Spotify OAuth 2.0 PKCE authentication with token caching and lifecycle commands**,
So that **every subsequent CLI command can make authenticated Spotify API requests without prompting the user to log in again**.

## Goals

1. Scaffold the Python project with `pyproject.toml`, Typer entry point, and package structure matching SPEC-001
2. Implement OAuth 2.0 Authorization Code + PKCE flow via spotipy, caching tokens at `~/.config/spotify-cli/.cache` with permissions 600
3. Expose `auth login`, `auth status`, and `auth logout` commands with structured JSON output and semantic exit codes

## Success Criteria

- [ ] `uv run spotify-cli --help` outputs a `Usage:` block and exits 0 in ≤500ms
- [ ] `spotify-cli auth login` completes the PKCE flow end-to-end and writes a token cache readable by spotipy
- [ ] A second invocation of any authenticated command does not open a browser (silent refresh)
- [ ] `spotify-cli auth login --no-browser` works in a headless/SSH environment
- [ ] `spotify-cli auth status` returns correct JSON for all three states: `valid`, `expired`, `missing`
- [ ] `spotify-cli auth logout` deletes the cache file; running it twice does not error
- [ ] Missing `SPOTIFY_CLIENT_ID` exits with code 2 and structured JSON on stderr
- [ ] `uv run pytest tests/auth/` passes with ≥80% coverage (TC-01 through TC-08)

## User Stories

| ID | Story | Points | Priority | Status |
|----|-------|--------|----------|--------|
| [E1-S1](../Stories/E1-S1_Project-Scaffold.md) | Project Scaffold — pyproject.toml, package structure, Typer entry point | 2 | High | To Do |
| [E1-S2](../Stories/E1-S2_Spotify-Client-Factory.md) | Spotify Client Factory — shared SpotifyPKCE factory, CACHE_PATH, env var guard | 2 | High | To Do |
| [E1-S3](../Stories/E1-S3_Auth-Login-Command.md) | Auth Login Command — PKCE browser flow, --no-browser headless mode | 3 | High | To Do |
| [E1-S4](../Stories/E1-S4_Auth-Status-Logout-Tests.md) | Auth Status & Logout + Tests — status/logout commands, full TC-01–TC-08 test suite | 3 | High | To Do |

**Total**: 10 story points

## Technical Approach

### Overview

Use `spotipy ≥2.25.1` for the PKCE OAuth flow — the library handles browser launch, local callback server on `http://127.0.0.1:9090/callback`, PKCE challenge/verifier generation, token exchange, and silent refresh. `CacheFileHandler` writes the token cache at `~/.config/spotify-cli/.cache` with 600 permissions (CVE-2025-27154 fix). `typer` provides the CLI framework with automatic `--help` generation and sub-app registration.

### Key Components

- `core/spotify_client.py`: Single source of truth for `CACHE_PATH`, `SCOPES`, `REDIRECT_URI`, `get_auth_manager()` factory, and `require_client_id()` guard
- `auth/commands.py`: `login`, `status`, `logout` command implementations — owns CLI flags, JSON output formatting, and exit codes
- `main.py`: Root Typer app; registers `auth` sub-app; exposes `--version` and `--help` / `-h`
- `tests/auth/test_auth_commands.py`: Unit tests using Typer `CliRunner` and mocked spotipy — no live API calls

### Technical Notes

- `spotipy ≥2.25.1` is a hard minimum — earlier versions do not enforce 600 permissions on `.cache` (CVE-2025-27154)
- `typer.Exit(code=2)` is used for missing env vars — cleanly exits without traceback and is catchable in tests
- Typer `CliRunner` merges stderr into `.output` by default; use subprocess for tests that need stderr separation
- `CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)` is called in `get_auth_manager()` before any write

## Dependencies

**Blocks**:
- EP-002: Discography Browse — requires authenticated SpotifyPKCE client
- EP-003: Playlist Creation — requires authenticated session

**Depends On**:
- None — this is the foundation epic

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redirect URI not registered in Spotify developer dashboard | H | Document required setup in README; verify during manual test phase |
| spotipy version below 2.25.1 installed by default | H | Pin `spotipy>=2.25.1` in `pyproject.toml` |
| `SPOTIFY_CLIENT_SECRET` required by spotipy even for PKCE | M | Include in env var guard documentation; add to error message |
| Typer CliRunner stderr merge masks exit-code-2 tests | L | Use subprocess for TC-02 stderr-separation assertion |

## Acceptance Criteria (Epic-Level)

- [ ] All four stories (E1-S1 through E1-S4) are marked Done
- [ ] `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80` passes
- [ ] Manual verification: `stat -f "%A" ~/.config/spotify-cli/.cache` shows `600` after login
- [ ] All auth commands exit 0 on success; missing env var exits 2

## Related Documentation

- [SPEC-001: Auth Login](../../_Design/04_Specs/SPEC-001__auth-login.md)
- [ADR-001: Authentication Flow — OAuth 2.0 Authorization Code with PKCE](../../_Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md)
- [Product Backlog](../Backlog/Product-Backlog.md)

## Notes

- This epic is the critical path for the entire project — EP-002 and EP-003 cannot proceed without it
- The `--version` flag (NFR-12) is a root-level concern implemented in E1-S1 alongside project scaffold, not a separate story
- Token cache location `~/.config/spotify-cli/.cache` is shared by all four stories — centralised in `core/spotify_client.py`

---

**Created**: 2026-06-04
**Last Updated**: 2026-06-04
