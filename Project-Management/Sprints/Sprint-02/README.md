# Sprint-02: Auth Commands End-to-End

**Goal**: `spotify-cli auth login`, `auth status`, and `auth logout` all work correctly with structured JSON output; TC-01 through TC-08 from SPEC-001 §2.6 pass with ≥80% coverage.

**Status**: ⏳ Planned
**Start**: TBD
**Developer**: Orlando Bruno
**Branch**: `sprint/2026-W23`
**PR**: https://github.com/orbruno/spotify-cli/pull/1

---

## Committed Stories

| Story | Title | Epic | Pts |
|-------|-------|------|-----|
| E1-S3 | Auth Login Command — PKCE browser flow, --no-browser headless mode | EP-001 | 3 |
| E1-S4 | Auth Status & Logout + Tests — status/logout commands, full TC-01–TC-08 test suite | EP-001 | 3 |

**Total committed**: 6pts

---

## Sprint Notes

**Path convention:**
- PM artifacts: `Project-Management/` (from project root)
- Code command root: `./` (project root — `pyproject.toml` and `spotify_cli/` both at root)
- Design docs: `_Design/` (sibling of `Project-Management/` at project root)
- Sprint-02 builds directly on the Sprint-01 scaffold: `spotify_cli/main.py`, `spotify_cli/core/spotify_client.py`, `spotify_cli/auth/commands.py` (stubs), and `tests/auth/test_auth_commands.py` (TC-02 only)

**What this sprint implements:**
- `login()` command body in `spotify_cli/auth/commands.py` (replaces `NotImplementedError` stub)
- `status()` and `logout()` commands added to `spotify_cli/auth/commands.py`
- Complete TC-01 through TC-08 test suite in `tests/auth/test_auth_commands.py`

**Conflict resolved — logout no-cache response key:**
- SPEC-001 §2.6 TC-07 and §3.3 test code use `{"status": "no_cache"}`
- E1-S4 AC and sprint backlog notes both specify `{"status": "no_session"}`
- **Resolution**: USE `"no_session"` — user explicitly flagged this in story notes and chose story over spec. SPEC-001 should be updated after this sprint.

**Conflict resolved — login output schema:**
- SPEC-001 §3.2 code example outputs `{"status": "authenticated"}` (no `cache_path`)
- E1-S3 story outputs `{"status": "authenticated", "cache_path": str(CACHE_PATH)}`
- **Resolution**: USE story form — test assertions use key-check (`["status"] == "authenticated"`), not equality, so the extra field is safe.

**Conflict resolved — `get_access_token` call:**
- SPEC-001 §3.2 uses `get_access_token()` (no args)
- E1-S3 story uses `get_access_token(as_dict=False)` to suppress return dict overhead
- **Resolution**: USE `as_dict=False` per story.

**No new dependencies** — `spotipy>=2.25.1` and `typer>=0.12.0` are already in `pyproject.toml`.

**No ADR promotions needed** — ADR-001 is already Accepted.

**Pre-sprint action**: SPEC-001 §1.10 still references `SPOTIFY_CLIENT_SECRET` as required. This is misleading for PKCE. Should be updated to "Not required for PKCE — only `SPOTIFY_CLIENT_ID` needed." Update SPEC-001 before or during this sprint.

---

## Definition of Done (Sprint Level)

- [ ] `uv run spotify-cli auth login --help` shows `Usage:` block with `-h` equivalent, exits 0
- [ ] `uv run spotify-cli auth status --help` shows `Usage:` block, exits 0
- [ ] `uv run spotify-cli auth logout --help` shows `Usage:` block, exits 0
- [ ] `SPOTIFY_CLIENT_ID="" uv run spotify-cli auth login` exits 2 with JSON containing `error`, `reason`, `suggestion`, `help` keys on stderr
- [ ] `uv run pytest tests/auth/ -v --no-cov` — all 8 TCs pass (TC-01 through TC-08)
- [ ] `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80 -o addopts=''` exits 0
- [ ] No live Spotify API calls anywhere in the test suite
- [ ] `auth logout` with no cache → `{"status": "no_session"}`, exit 0 (idempotent)
- [ ] `auth status` returns correct JSON for all three states: `valid`, `expired`, `missing`
