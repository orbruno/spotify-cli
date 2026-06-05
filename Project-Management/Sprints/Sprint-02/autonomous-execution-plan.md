# Sprint-02 Autonomous Execution Plan

**Sprint Goal**: `spotify-cli auth login`, `auth status`, and `auth logout` all work correctly with structured JSON output; TC-01 through TC-08 from SPEC-001 §2.6 pass with ≥80% coverage.
**Mode**: Fully autonomous — `--dangerously-skip-permissions`, no human intervention.
**Total**: 2 stories, 6pts. Builds on top of Sprint-01 codebase (`spotify_cli/`).

---

## How to Use This Plan

```bash
# Recommended: isolated worktree (keeps main checkout clean)
claude --worktree --dangerously-skip-permissions \
  "Read Project-Management/Sprints/Sprint-02/autonomous-execution-plan.md and execute it wave by wave."

# Alternative: run directly in working tree
claude --dangerously-skip-permissions \
  "Read Project-Management/Sprints/Sprint-02/autonomous-execution-plan.md and execute it wave by wave."
```

---

## Architecture Source of Truth

Read these files before writing any code, in priority order:

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `_Design/04_Specs/SPEC-001__auth-login.md` | Auth command interfaces, output schemas, TC definitions |
| 2 | `_Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md` | PKCE decision, `SpotifyPKCE` key interfaces, redirect URI |
| 3 | `Project-Management/Stories/E1-S3_Auth-Login-Command.md` | E1-S3 AC, DoD, exact implementation code |
| 4 | `Project-Management/Stories/E1-S4_Auth-Status-Logout-Tests.md` | E1-S4 AC, DoD, complete test scaffold |
| 5 | `spotify_cli/auth/commands.py` | Current stub — `login()` is NotImplementedError, `status()`/`logout()` are NotImplementedError |
| 6 | `spotify_cli/core/spotify_client.py` | Fully implemented — `CACHE_PATH`, `SCOPES`, `REDIRECT_URI`, `require_client_id()`, `get_auth_manager()` |
| 7 | `spotify_cli/main.py` | Entry point — `auth login/status/logout` already registered |
| 8 | `tests/auth/test_auth_commands.py` | Sprint-01 tests: TC-02 + 2 factory tests — Wave 1 E1-S4 replaces this entirely |

---

## Conflict Resolution Rules

| Conflict | Resolution | Reference |
|----------|-----------|-----------|
| `{"status": "no_cache"}` (SPEC-001 §2.6 TC-07, §3.3 code) vs `{"status": "no_session"}` (E1-S4 AC) | USE `"no_session"` — explicitly flagged in story notes; SPEC-001 needs updating after sprint | `Stories/E1-S4_Auth-Status-Logout-Tests.md` §Notes |
| `{"status": "authenticated"}` (SPEC-001 §3.2) vs `{"status": "authenticated", "cache_path": "..."}` (E1-S3 story) | USE story form with `cache_path` — test assertions use key check `["status"]`, not equality | `Stories/E1-S3_Auth-Login-Command.md` §Technical Notes |
| `get_access_token()` (SPEC-001 §3.2) vs `get_access_token(as_dict=False)` (E1-S3 story) | USE `as_dict=False` — suppresses return dict overhead | `Stories/E1-S3_Auth-Login-Command.md` §Notes |

---

## Pre-flight Assertions

Run before dispatching any subagent. Stop and report if any check fails.

```bash
set -e
cd /Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli

# Sprint-01 core files must exist
test -f spotify_cli/main.py          || { echo "MISSING: spotify_cli/main.py (Sprint-01 not complete)"; exit 1; }
test -f spotify_cli/core/spotify_client.py || { echo "MISSING: spotify_cli/core/spotify_client.py"; exit 1; }
test -f spotify_cli/auth/commands.py || { echo "MISSING: spotify_cli/auth/commands.py"; exit 1; }
test -f tests/auth/test_auth_commands.py || { echo "MISSING: tests/auth/test_auth_commands.py"; exit 1; }

# Design docs referenced by this sprint must exist
test -f _Design/04_Specs/SPEC-001__auth-login.md || { echo "MISSING: SPEC-001"; exit 1; }
test -f _Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md || { echo "MISSING: ADR-001"; exit 1; }

# uv is available
which uv > /dev/null || { echo "MISSING: uv not found in PATH"; exit 1; }

# Sprint-01 tests still pass (TC-02 + 2 factory tests)
uv run pytest tests/auth/ -x -q --no-cov
echo "Pre-flight passed."
```

---

## Story → Wave Mapping

```
Wave 1  │  E1-S3 ─── Auth Login Command (login() implementation + TC-01, TC-03)
(seq)   │
        │  E1-S4 ─── Auth Status & Logout + Tests (status(), logout(), TC-01–TC-08 full suite)
        │            [MUST run after E1-S3 — both modify commands.py; TC-01/TC-03/TC-08 test login()]
        │
Wave 2  │  Integration verification
        │  (no code changes — run full suite, smoke test help commands, report only)
```

---

## Per-Wave Subagent Prompts

---

### Wave 1 — Agent 1: E1-S3 Auth Login Command

```
You are implementing E1-S3: Auth Login Command for the spotify-cli project.

READ FIRST:
- Project-Management/Stories/E1-S3_Auth-Login-Command.md   (AC, DoD, exact code)
- _Design/04_Specs/SPEC-001__auth-login.md §2.3, §3.2      (component interfaces)
- _Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md §5  (key interfaces)
- spotify_cli/auth/commands.py                              (current stub — modify login() only)
- spotify_cli/core/spotify_client.py                        (read only — provides CACHE_PATH, get_auth_manager, require_client_id)
- tests/auth/test_auth_commands.py                          (existing TC-02 + 2 factory tests — APPEND TC-01 and TC-03)

CONFLICT RESOLUTION:
- USE {"status": "authenticated", "cache_path": str(CACHE_PATH)} — NOT {"status": "authenticated"} alone
  WHY: E1-S3 story specifies cache_path for transparency; test assertions use key-check not equality
- USE auth_manager.get_access_token(as_dict=False) — NOT get_access_token() without args
  WHY: suppresses return dict overhead per E1-S3 story §Notes

IMPLEMENT in spotify_cli/auth/commands.py:
Replace ONLY the login() function. Keep the existing imports. Add json and CACHE_PATH imports.
Final login() implementation:

```python
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


def status() -> None:
    """
    Print current token status as JSON.

    Usage: spotify-cli auth status
    Example: spotify-cli auth status
    """
    raise NotImplementedError("Implemented in E1-S4")


def logout() -> None:
    """
    Delete cached Spotify tokens.

    Usage: spotify-cli auth logout
    Example: spotify-cli auth logout
    """
    raise NotImplementedError("Implemented in E1-S4")
```

WRITE TESTS — APPEND these two functions to tests/auth/test_auth_commands.py:
(After the existing tests. Do NOT remove existing tests.)

```python
# TC-01: login success
def test_login_success():
    """TC-01: auth login with SPOTIFY_CLIENT_ID set exits 0 with authenticated JSON."""
    from unittest.mock import MagicMock, patch
    mock_manager = MagicMock()
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    assert json.loads(result.output)["status"] == "authenticated"


# TC-03: --no-browser passes open_browser=False
def test_login_no_browser():
    """TC-03: --no-browser passes open_browser=False to SpotifyPKCE factory."""
    from unittest.mock import MagicMock, patch
    mock_manager = MagicMock()
    with patch(
        "spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager
    ) as mock_pkce:
        result = runner.invoke(app, ["auth", "login", "--no-browser"])
    assert result.exit_code == 0
    _, kwargs = mock_pkce.call_args
    assert kwargs.get("open_browser") is False
```

VERIFY: cd /Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli && uv run pytest tests/auth/ -x -q --no-cov
All 4 tests must pass (TC-01, TC-02, TC-03, plus test_get_auth_manager_creates_cache_directory). Exit 0.
```

---

### Wave 1 — Agent 2: E1-S4 Auth Status & Logout + Tests

```
You are implementing E1-S4: Auth Status & Logout + Tests for the spotify-cli project.
This agent MUST run after Wave 1 Agent 1 (E1-S3) completes — login() must already be implemented.

READ FIRST:
- Project-Management/Stories/E1-S4_Auth-Status-Logout-Tests.md   (AC, DoD, complete test scaffold)
- _Design/04_Specs/SPEC-001__auth-login.md §2.4, §2.6            (output schemas, TC-01–TC-08 table)
- spotify_cli/auth/commands.py                                    (current state: login() implemented, status()/logout() are NotImplementedError)
- tests/auth/test_auth_commands.py                                (current state after E1-S3 — will be REPLACED entirely)

CONFLICT RESOLUTION:
- USE {"status": "no_session"} for logout with no cache — NOT {"status": "no_cache"}
  WHY: E1-S4 story AC and backlog notes explicitly override SPEC-001 §2.6 TC-07 and §3.3 test code.
       SPEC-001 will be updated after this sprint.
- TC-07 test MUST assert: assert json.loads(result.output) == {"status": "no_session"}
  Not "no_cache" — the test will fail if you use the SPEC value.

IMPLEMENT — REPLACE entire spotify_cli/auth/commands.py with this complete file:

```python
import json
import time
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


def status() -> None:
    """
    Print current token status as JSON.

    Usage: spotify-cli auth status
    Example: spotify-cli auth status
    """
    if not CACHE_PATH.exists():
        typer.echo(json.dumps({"status": "missing"}))
        raise typer.Exit(code=0)

    require_client_id()
    auth_manager = get_auth_manager(open_browser=False)
    token_info = auth_manager.cache_handler.get_cached_token()

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
```

WRITE TESTS — REPLACE entire tests/auth/test_auth_commands.py with this complete scaffold:

```python
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from spotify_cli.main import app
from spotify_cli.core.spotify_client import get_auth_manager

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
    """TC-04: auth status with valid cached token returns status=valid."""
    mock_token = {
        "access_token": "tok",
        "expires_at": time.time() + 3600,
        "scope": "playlist-modify-public user-read-private",
    }
    mock_handler = MagicMock()
    mock_handler.get_cached_token.return_value = mock_token
    mock_manager = MagicMock()
    mock_manager.cache_handler = mock_handler

    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path, \
         patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager):
        mock_path.exists.return_value = True
        result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["status"] == "valid"
    assert parsed["expires_in_seconds"] > 0


# TC-05: status with no cache file
def test_status_missing_cache():
    """TC-05: auth status with no cache file returns status=missing."""
    with patch("spotify_cli.auth.commands.CACHE_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "missing"}


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


# TC-08: silent refresh — default login uses open_browser=True (not headless)
def test_silent_refresh():
    """TC-08: auth login default does not disable browser; mock manager handles refresh."""
    expired_token = {
        "access_token": "old",
        "expires_at": time.time() - 60,
        "scope": "playlist-modify-public",
        "refresh_token": "refresh-tok",
    }
    fresh_token = {
        "access_token": "new",
        "expires_at": time.time() + 3600,
        "scope": "playlist-modify-public",
    }
    mock_handler = MagicMock()
    mock_handler.get_cached_token.side_effect = [expired_token, fresh_token]
    mock_manager = MagicMock()
    mock_manager.cache_handler = mock_handler
    mock_manager.get_access_token.return_value = "new"

    with patch("spotify_cli.core.spotify_client.SpotifyPKCE", return_value=mock_manager) as mock_pkce:
        result = runner.invoke(app, ["auth", "login"])

    assert result.exit_code == 0
    _, kwargs = mock_pkce.call_args
    assert kwargs.get("open_browser") is not False  # open_browser=True by default (not headless)


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
```

VERIFY step 1: cd /Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli && uv run pytest tests/auth/ -x -q --no-cov
All 10 tests must pass (TC-01 through TC-08 + 2 factory tests). Exit 0.

VERIFY step 2: cd /Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli && uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80 -o addopts=''
Coverage ≥80% for spotify_cli/auth and spotify_cli/core. Exit 0.
```

---

### Wave 2 — Integration Verification

```
You are the integration verification agent for Sprint-02 of spotify-cli.
DO NOT make any code changes. Run commands, observe results, and report.

VERIFY each item below. Report PASS or FAIL with output for each.

cd /Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli

1. Full test suite with coverage:
   uv run pytest tests/auth/ -v --no-cov
   EXPECTED: 10 tests pass, 0 failures

2. Coverage gate:
   uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80 -o addopts=''
   EXPECTED: coverage ≥80%, exit 0

3. Help commands:
   uv run spotify-cli --help           (must show Usage: and list auth subgroup, exit 0)
   uv run spotify-cli auth --help      (must show login, status, logout, exit 0)
   uv run spotify-cli auth login --help  (must show --no-browser option and Usage:/Example: blocks, exit 0)
   uv run spotify-cli auth status --help (must show Usage: block, exit 0)
   uv run spotify-cli auth logout --help (must show Usage: block, exit 0)

4. Missing env var guard:
   SPOTIFY_CLIENT_ID="" uv run spotify-cli auth login
   EXPECTED: exit code 2, JSON with error/reason/suggestion/help keys

5. Status with no cache:
   uv run spotify-cli auth status
   EXPECTED: {"status": "missing"}, exit 0 (assuming no real cache file exists)

6. Logout idempotency:
   uv run spotify-cli auth logout
   EXPECTED: {"status": "no_session"}, exit 0 (idempotent — safe to run without cache)

Report a summary:
  - Tests: N/10 passed
  - Coverage: N%
  - Help commands: PASS/FAIL
  - Missing env var guard: PASS/FAIL
  - Status/Logout smoke tests: PASS/FAIL
  - Overall: READY TO MERGE or BLOCKERS FOUND (list them)
```

---

## Sprint Completion Checklist

After Wave 2 integration verification passes, the orchestrator updates all PM artifacts:

For E1-S3:
- Update `Project-Management/Stories/E1-S3_Auth-Login-Command.md` Status → `✅ Done`
- Check all Definition of Done checkboxes

For E1-S4:
- Update `Project-Management/Stories/E1-S4_Auth-Status-Logout-Tests.md` Status → `✅ Done`
- Check all Definition of Done checkboxes

Update `Project-Management/Sprints/Sprint-02/sprint-backlog.md`:
- Change E1-S3 and E1-S4 Status → `✅ Done`
- Update Points Tracker: Done = 6
- Append Daily Progress entry with today's date and outcome summary

Update `Project-Management/Backlog/Product-Backlog.md`:
- Mark E1-S3 and E1-S4 as Done

Update `Project-Management/README.md`:
- Change `Current Sprint` link → `Sprints/Sprint-02/sprint-backlog.md`
- Change `Current Status` → "Sprint-02 complete — auth commands end-to-end working; EP-001 complete"
- Update EP-001 Progress Summary → 100%

Note for future sprint planning:
- Update SPEC-001 §2.6 TC-07 from `{"status": "no_cache"}` to `{"status": "no_session"}` and §3.3 test code accordingly
- Update SPEC-001 §1.10 to remove `SPOTIFY_CLIENT_SECRET` as a required dependency for PKCE

---

## Autonomous Decision Reference

| Decision | Answer | Source |
|----------|--------|--------|
| Logout no-cache response key | `"no_session"` NOT `"no_cache"` | E1-S4 story AC overrides SPEC-001 §2.6 TC-07 |
| Login success output | `{"status": "authenticated", "cache_path": str(CACHE_PATH)}` | E1-S3 story §Technical Notes |
| `get_access_token` call | `get_access_token(as_dict=False)` | E1-S3 story §Notes |
| Cache path | `~/.config/spotify-cli/.cache` via `CACHE_PATH` constant | `core/spotify_client.py:7` |
| Redirect URI | `http://127.0.0.1:9090/callback` | ADR-001 §1 (localhost banned Nov 2025) |
| Required env var | `SPOTIFY_CLIENT_ID` only (no `SPOTIFY_CLIENT_SECRET` for PKCE) | ADR-001 §4 |
| Missing env var exit code | `2` with structured JSON on stderr | SPEC-001 §1.5 SFR-09 |
| `status()` env var check | Does NOT call `require_client_id()` before cache file check — missing cache needs no env var | E1-S4 story §Notes |
| How to patch CACHE_PATH in tests | `patch("spotify_cli.auth.commands.CACHE_PATH")` — commands.py imports it directly | E1-S4 test scaffold |
| Coverage pytest command | `uv run pytest tests/auth/ --cov=spotify_cli/auth --cov=spotify_cli/core --cov-fail-under=80 -o addopts=''` | pyproject.toml has no addopts — `-o addopts=''` is harmless safety measure |
| Test runner | `uv run pytest` always — never bare `pytest` | Global rules (uv only) |
