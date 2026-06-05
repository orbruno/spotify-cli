# Sprint 02 Backlog

**Sprint**: Sprint-02
**Date**: TBD
**Sprint Goal**: `spotify-cli auth login`, `auth status`, and `auth logout` all work correctly; TC-01 through TC-08 from SPEC-001 pass.
**Total Points**: 6
**Status**: Planned

---

## Committed Stories

| ID | Story | Points | Status |
|----|-------|--------|--------|
| E1-S3 | Auth Login Command — PKCE browser flow, --no-browser headless mode | 3 | To Do |
| E1-S4 | Auth Status & Logout + Tests — status/logout commands, full TC-01–TC-08 test suite | 3 | To Do |

**Total**: 6 points

---

## Task Breakdown

### E1-S3 — Auth Login Command (3 pts)

- [ ] Implement `login(no_browser: bool)` command in `spotify_cli/auth/commands.py` using `typer.Option` for `--no-browser`
- [ ] Call `require_client_id()` first in `login()` — exits 2 if env var missing
- [ ] Call `get_auth_manager(open_browser=not no_browser).get_access_token(as_dict=False)` — spotipy handles browser launch, callback server, PKCE exchange, and cache write
- [ ] On success, `typer.echo(json.dumps({"status": "authenticated", "cache_path": str(CACHE_PATH)}))` and exit 0
- [ ] Add TC-01 test (mock success, assert JSON + exit 0) to `tests/auth/test_auth_commands.py`
- [ ] Add TC-03 test (`--no-browser`, assert `open_browser=False` passed to `SpotifyPKCE`) to `tests/auth/test_auth_commands.py`
- [ ] Manual verify: `uv run spotify-cli auth login` opens browser and writes cache
- [ ] Manual verify: `stat -f "%A" ~/.config/spotify-cli/.cache` shows `600`

### E1-S4 — Auth Status & Logout + Tests (3 pts)

- [ ] Implement `status()` in `auth/commands.py`: check `CACHE_PATH.exists()`; if missing output `{"status": "missing"}`; otherwise read cached token, compute `expires_in = int(token_info["expires_at"] - time.time())`, set `state = "valid" if expires_in > 0 else "expired"`, include `scopes` only when valid
- [ ] Implement `logout()` in `auth/commands.py`: if `CACHE_PATH.exists()` → `CACHE_PATH.unlink()` + `{"status": "logged_out"}`; else → `{"status": "no_session"}`; always exit 0 (idempotent)
- [ ] Scaffold `tests/auth/test_auth_commands.py` with `CliRunner`, `autouse` fixture for `SPOTIFY_CLIENT_ID`, and all 8 test cases (TC-01 through TC-08) using `unittest.mock.patch`
- [ ] Implement TC-04: status with valid token → `status: "valid"` and positive `expires_in_seconds`
- [ ] Implement TC-05: status with no cache file → `{"status": "missing"}`, exit 0
- [ ] Implement TC-06: logout with cache present → deletes file, `{"status": "logged_out"}`, exit 0
- [ ] Implement TC-07: logout with no cache file → `{"status": "no_session"}`, exit 0
- [ ] Implement TC-08: silent refresh — expired token refreshed without opening browser
- [ ] Run coverage gate: `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80`

---

## Acceptance Criteria Summary

**E1-S3**:
- First run opens browser and captures redirect at `http://127.0.0.1:9090/callback`
- Token written to `~/.config/spotify-cli/.cache` with permissions 600 (spotipy ≥2.25.1)
- Subsequent runs within TTL do not open browser (silent refresh via spotipy)
- `--no-browser` passes `open_browser=False` to factory
- Success output: `{"status": "authenticated", "cache_path": "~/.config/spotify-cli/.cache"}` on stdout, exit 0
- `SPOTIFY_CLIENT_ID` missing → exit 2 with structured JSON on stderr
- TC-01 and TC-03 pass via `uv run pytest`

**E1-S4**:
- `auth status` with valid cached token → JSON with `status: "valid"` and positive `expires_in_seconds`, exit 0
- `auth status` with expired token → JSON with `status: "expired"` and negative `expires_in_seconds`, exit 0
- `auth status` with no cache file → `{"status": "missing"}`, exit 0
- `auth logout` with cache present → deletes file, `{"status": "logged_out"}`, exit 0
- `auth logout` with no cache file → `{"status": "no_session"}`, exit 0 (idempotent)
- All TC-01 through TC-08 from SPEC-001 §2.6 pass via `uv run pytest tests/auth/`
- No live Spotify API calls in the test suite
- Coverage ≥80%: `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80`

---

## Definition of Done

- [ ] All code implemented following conventions (Python, Typer, uv)
- [ ] All acceptance criteria met for E1-S3 and E1-S4
- [ ] All TC-01 through TC-08 passing via `uv run pytest tests/auth/ -v`
- [ ] Coverage ≥80% for `spotify_cli/auth` and `spotify_cli/core`
- [ ] No live Spotify API calls in test suite
- [ ] Self-reviewed
- [ ] No known bugs or issues

---

## Risks / Notes

- Dependency: Sprint-01 must be complete before starting — `main.py` entry point and `core/spotify_client.py` factory must exist
- `CliRunner` from Typer merges stderr into `.output` by default — TC-02 asserts on `.output`, not `.stderr`; use subprocess for tests that must separately assert stderr
- SPEC-001 §2.6 TC-07 uses `{"status": "no_cache"}` but stories specify `{"status": "no_session"}` — follow the story; update SPEC-001 if needed
- `status()` does not call `require_client_id()` before checking for the cache file — reading a missing cache does not require env vars

---

**Last Updated**: 2026-06-05
**Status**: Planned
