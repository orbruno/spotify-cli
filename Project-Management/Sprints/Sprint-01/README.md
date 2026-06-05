# Sprint-01: Project Scaffold + Client Factory

**Goal**: Running `uv run spotify-cli --help` works, `SpotifyPKCE` client factory is wired up with `CACHE_PATH`, and `require_client_id()` guard is in place.

**Status**: ⏳ Planned
**Start**: 2026-06-05
**Developer**: Orlando Bruno

---

## Committed Stories

| Story | Title | Epic | Pts |
|-------|-------|------|-----|
| E1-S1 | Project Scaffold — pyproject.toml, package structure, Typer entry point | EP-001 | 2 |
| E1-S2 | Spotify Client Factory — shared SpotifyPKCE factory, CACHE_PATH, env var guard | EP-001 | 2 |

**Total committed**: 4pts

---

## Sprint Notes

**Path convention:**
- PM artifacts: `Project-Management/`
- Code command root: `./` (project root — `pyproject.toml` lives here)
- Design docs: `_Design/` (sibling of `Project-Management/`)
- Sprint-01 creates the entire codebase from scratch — no prior implementation to build on

**What this sprint establishes:**
- The `pyproject.toml` with `spotipy>=2.25.1` and `typer>=0.12.0` runtime deps and `pytest>=8.0`/`pytest-cov>=5.0` dev deps
- Package skeleton: `spotify_cli/`, `spotify_cli/auth/`, `spotify_cli/core/`, `tests/`, `tests/auth/` with `__init__.py` files
- `spotify_cli/main.py` — root Typer app, `auth` sub-app registered, `login`/`status`/`logout` stubs wired, `--version` callback
- `spotify_cli/core/spotify_client.py` — `CACHE_PATH`, `SCOPES`, `REDIRECT_URI` constants; `get_auth_manager()` and `require_client_id()` functions
- `tests/auth/test_auth_commands.py` — TC-02 unit test (missing env var → exit 2 + JSON on stderr)

**Authentication factory decisions (from ADR-001 + SPEC-001):**
- Use `CacheFileHandler(cache_path=str(CACHE_PATH))` wrapper — NOT bare `cache_path=` kwarg on `SpotifyPKCE` (ADR key interface uses bare form; story + spec override with `CacheFileHandler`)
- Test for TC-02 lives in `tests/auth/test_auth_commands.py` — NOT `tests/core/` (SPEC-001 §2.1 file tree has no `tests/core/`)
- Redirect URI fixed: `http://127.0.0.1:9090/callback` — `localhost` banned by Spotify since Nov 2025 (ADR-001 §1)
- `spotipy>=2.25.1` required for CVE-2025-27154 fix (600-permission enforcement on cache file)

**Deferred work:**
- `auth login` browser flow implementation → E1-S3 (Sprint-02)
- `auth status` and `auth logout` command bodies → E1-S4 (Sprint-02)
- TC-01, TC-03 through TC-08 tests → E1-S3/E1-S4 (Sprint-02)

**No ADR promotions needed** — ADR-001 is already Accepted.

---

## Definition of Done (Sprint Level)

- [ ] `uv run spotify-cli --help` outputs a `Usage:` block and exits 0
- [ ] `uv run spotify-cli --version` prints version string and exits 0
- [ ] `-h` is equivalent to `--help` at all levels: `uv run spotify-cli -h`, `uv run spotify-cli auth -h`, `uv run spotify-cli auth login -h`
- [ ] `uv run pytest` runs without import errors (even with stubs in place)
- [ ] Package structure matches SPEC-001 §2.1 file tree exactly
- [ ] `SPOTIFY_CLIENT_ID` unset → exits 2 with structured JSON on stderr containing `error`, `reason`, `suggestion`, and `help` keys
- [ ] `CACHE_PATH` resolves to `~/.config/spotify-cli/.cache`
- [ ] Cache directory created automatically via `mkdir(parents=True, exist_ok=True)` if missing
- [ ] `get_auth_manager(open_browser=False)` passes `open_browser=False` through to `SpotifyPKCE`
- [ ] TC-02 unit test written and passing: `uv run pytest tests/auth/ -x -q --no-cov` exits 0
