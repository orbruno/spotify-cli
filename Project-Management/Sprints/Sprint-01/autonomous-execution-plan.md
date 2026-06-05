# Sprint-01 Autonomous Execution Plan

**Sprint Goal**: Running `uv run spotify-cli --help` works, `SpotifyPKCE` client factory is wired up with `CACHE_PATH`, and `require_client_id()` guard is in place.
**Mode**: Fully autonomous — `--dangerously-skip-permissions`, no human intervention.
**Total**: 2 stories, 4pts. Sprint-01 creates the entire codebase from scratch — there is no prior baseline.

---

## How to Use This Plan

```bash
cd /Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli

# Recommended: isolated worktree (keeps main checkout clean)
claude --worktree --dangerously-skip-permissions \
  "Read Project-Management/Sprints/Sprint-01/autonomous-execution-plan.md and execute it wave by wave."

# Alternative: run directly in working tree
claude --dangerously-skip-permissions \
  "Read Project-Management/Sprints/Sprint-01/autonomous-execution-plan.md and execute it wave by wave."
```

> If you use `--worktree`, the generated `.claude/worktrees/` directory is an execution artifact. Do not commit it. Confirm `.gitignore` contains `.claude/worktrees/` before running.

---

## Architecture Source of Truth

Read these files in this priority order **before writing a single line of code**:

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `_Design/04_Specs/SPEC-001__auth-login.md` | File tree (§2.1), component interfaces (§2.3), `pyproject.toml` content (§3.1), `spotify_client.py` content (§3.2), test scaffold (§3.4) — **overrides story wording on any conflict** |
| 2 | `_Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md` | Rationale for PKCE; redirect URI constraint (`127.0.0.1:9090`, not `localhost`); `spotipy>=2.25.1` requirement |
| 3 | `Project-Management/Stories/E1-S1_Project-Scaffold.md` | Acceptance criteria, DoD, exact `pyproject.toml` and `main.py` code |
| 4 | `Project-Management/Stories/E1-S2_Spotify-Client-Factory.md` | Acceptance criteria, DoD, exact `spotify_client.py` code, TC-02 test details |
| 5 | `Project-Management/Sprints/Sprint-01/README.md` | Sprint notes, path convention, conflict resolution summary |

---

## Conflict Resolution Rules

| Conflict | Resolution | Reference |
|----------|-----------|-----------|
| ADR-001 §5 key interface passes `cache_path=...` directly to `SpotifyPKCE` constructor | USE `CacheFileHandler(cache_path=str(CACHE_PATH))` wrapper as shown in SPEC-001 §3.2 and E1-S2 story — both are more specific and authoritative than the ADR overview | `_Design/04_Specs/SPEC-001__auth-login.md` §3.2 |
| Pre-confirmed context mentions `tests/core/test_spotify_client.py` as TC-02 test location | USE `tests/auth/test_auth_commands.py` — SPEC-001 §2.1 file tree has no `tests/core/` directory; E1-S2 story explicitly names `tests/auth/test_auth_commands.py` | `Project-Management/Stories/E1-S2_Spotify-Client-Factory.md` §Technical Notes |
| `main.py` code snippet in E1-S1 story omits `--version` callback | INCLUDE `--version` callback in `main.py` — E1-S1 AC #2, NFR-12, and SPEC-001 §3.1 T-03 all require it; the story text and description confirm it | `Project-Management/Stories/E1-S1_Project-Scaffold.md` §Description |
| `SPOTIFY_CLIENT_SECRET` listed as required in SPEC-001 §1.10 and possibly EP-001 | **Do not require, check, or document `SPOTIFY_CLIENT_SECRET` in Sprint-01.** PKCE requires only `SPOTIFY_CLIENT_ID`. The secret field in SPEC-001 is a documentation error. | ADR-001 |

---

## Pre-flight Assertions

Run these checks before dispatching any wave subagent. Stop and report if any fail.

```bash
#!/usr/bin/env bash
set -e

PROJECT_ROOT="/Users/orlandobruno/Documents/Areas/Software-Dev/CLI-Tools/spotify-cli"
cd "$PROJECT_ROOT"

echo "=== Pre-flight Assertions for Sprint-01 ==="

# 1. Sprint-01 creates pyproject.toml — assert it does NOT already exist
if [ -f "pyproject.toml" ]; then
  echo "FAIL: pyproject.toml already exists. Sprint-01 should create it from scratch."
  echo "      If this is a re-run, remove pyproject.toml and the spotify_cli/ directory first."
  exit 1
else
  echo "PASS: pyproject.toml does not exist yet (correct for Sprint-01 first run)"
fi

# 2. uv is available
which uv > /dev/null 2>&1 && echo "PASS: uv is available at $(which uv)" || { echo "FAIL: uv not found on PATH"; exit 1; }

# 3. SPOTIFY_CLIENT_ID env var (warn only — Sprint-01 does not require live auth)
if [ -z "${SPOTIFY_CLIENT_ID}" ]; then
  echo "WARN: SPOTIFY_CLIENT_ID is not set. TC-02 tests for its absence, so this is expected during testing."
  echo "      Set it before running E1-S3 (auth login) in Sprint-02."
else
  echo "INFO: SPOTIFY_CLIENT_ID is set"
fi

# 4. Design docs exist
test -f "_Design/04_Specs/SPEC-001__auth-login.md" \
  && echo "PASS: SPEC-001 exists" \
  || { echo "FAIL: _Design/04_Specs/SPEC-001__auth-login.md not found"; exit 1; }

test -f "_Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md" \
  && echo "PASS: ADR-001 exists" \
  || { echo "FAIL: _Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md not found"; exit 1; }

# 5. Story files exist
test -f "Project-Management/Stories/E1-S1_Project-Scaffold.md" \
  && echo "PASS: E1-S1 story file exists" \
  || { echo "FAIL: Project-Management/Stories/E1-S1_Project-Scaffold.md not found"; exit 1; }

test -f "Project-Management/Stories/E1-S2_Spotify-Client-Factory.md" \
  && echo "PASS: E1-S2 story file exists" \
  || { echo "FAIL: Project-Management/Stories/E1-S2_Spotify-Client-Factory.md not found"; exit 1; }

echo ""
echo "=== All pre-flight checks passed. Proceed to Wave 0. ==="
```

---

## Story → Wave Mapping

```
Wave 0  │  E1-S1: Project Scaffold
         │  pyproject.toml, package skeleton (__init__.py files),
         │  stub files (auth/commands.py, core/spotify_client.py),
         │  main.py (Typer app + auth sub-app + --version callback)
         │  VERIFY: uv run spotify-cli --help exits 0
         │
Wave 1  │  E1-S2: Spotify Client Factory
(seq)    │  Fills core/spotify_client.py: CACHE_PATH, SCOPES, REDIRECT_URI,
         │  get_auth_manager(), require_client_id()
         │  Adds TC-02 test in tests/auth/test_auth_commands.py
         │  VERIFY: uv run pytest tests/auth/ -x -q --no-cov exits 0
         │
Wave 2  │  Integration verification (no code changes — report only)
         │  uv run spotify-cli --help contains "Usage:"
         │  uv run pytest -x -q --no-cov exits 0
```

---

## Per-Wave Subagent Prompts

---

### Wave 0 — Project Scaffold (E1-S1)

```
You are implementing E1-S1: Project Scaffold for the Spotify CLI project.

READ FIRST:
- Project-Management/Stories/E1-S1_Project-Scaffold.md   (acceptance criteria and DoD)
- _Design/04_Specs/SPEC-001__auth-login.md §2.1 and §3.1 (file tree and pyproject.toml — source of truth)
- _Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md §5 (key interfaces and constraints)

CONFLICT RESOLUTION:
- main.py MUST include a --version callback even though the code snippet in the story omits it.
  E1-S1 AC #2 requires `uv run spotify-cli --version` to print the version string and exit 0.
  NFR-12 is a root-level concern assigned to this story.

IMPLEMENT — create each file exactly as specified below:

---

FILE 1: pyproject.toml (create at project root)

[project]
name = "spotify-cli"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "spotipy>=2.25.1",
    "typer>=0.12.0",
]

[project.scripts]
spotify-cli = "spotify_cli.main:app"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

---

FILE 2: Create package skeleton (all empty files)

Run these commands exactly:
  mkdir -p spotify_cli/auth spotify_cli/core tests/auth
  touch spotify_cli/__init__.py
  touch spotify_cli/auth/__init__.py
  touch spotify_cli/core/__init__.py
  touch tests/__init__.py
  touch tests/auth/__init__.py

---

FILE 3: spotify_cli/auth/commands.py (stub — do NOT implement login/status/logout bodies)

import typer


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
    """
    raise NotImplementedError("Implemented in E1-S3")


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

---

FILE 4: spotify_cli/core/spotify_client.py (stub — do NOT implement functions yet)

# Implemented in E1-S2

---

FILE 5: spotify_cli/main.py

import typer
from spotify_cli.auth import commands as auth_commands

__version__ = "0.1.0"

app = typer.Typer(
    help="Spotify CLI — manage your Spotify account from the terminal.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
auth_app = typer.Typer(
    help="Authentication commands.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
# context_settings propagates to all subcommands registered on auth_app
# No per-command override needed unless a command uses a custom Context
app.add_typer(auth_app, name="auth")

auth_app.command("login")(auth_commands.login)
auth_app.command("status")(auth_commands.status)
auth_app.command("logout")(auth_commands.logout)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"spotify-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


if __name__ == "__main__":
    app()

---

AFTER creating all files, install dependencies:
  uv sync

VERIFY (all commands must exit 0):
  uv run spotify-cli --help && \
  uv run spotify-cli -h && \
  uv run spotify-cli auth --help && \
  uv run spotify-cli auth -h && \
  uv run spotify-cli auth login --help && \
  uv run spotify-cli auth login -h
  uv run spotify-cli --version

Confirm `uv run spotify-cli --help` and `uv run spotify-cli -h` both output text containing the word "Usage:" before marking Wave 0 complete.
```

---

### Wave 1 — Spotify Client Factory (E1-S2)

```
You are implementing E1-S2: Spotify Client Factory for the Spotify CLI project.

Wave 0 (project scaffold) must be complete before running this wave.
`pyproject.toml` and the `spotify_cli/` package skeleton must already exist.

READ FIRST:
- Project-Management/Stories/E1-S2_Spotify-Client-Factory.md   (acceptance criteria and DoD)
- _Design/04_Specs/SPEC-001__auth-login.md §2.3 and §3.2       (component interfaces — source of truth)
- _Design/03_ADR/ADR-001__sys__authentication-flow-pkce.md §5   (rationale for PKCE; redirect URI)
- spotify_cli/core/spotify_client.py                            (current stub — replace entirely)

CONFLICT RESOLUTION:
- USE CacheFileHandler(cache_path=str(CACHE_PATH)) — NOT bare cache_path= kwarg on SpotifyPKCE.
  ADR-001 §5 key interface omits CacheFileHandler; SPEC-001 §3.2 and E1-S2 story both use the
  CacheFileHandler wrapper. SPEC-001 is authoritative.
- TC-02 test MUST go in tests/auth/test_auth_commands.py — NOT tests/core/test_spotify_client.py.
  SPEC-001 §2.1 file tree has no tests/core/ directory. E1-S2 story §Technical Notes names
  tests/auth/test_auth_commands.py explicitly.
- Redirect URI is http://127.0.0.1:9090/callback — localhost is banned by Spotify since Nov 2025.

WRITE TEST FIRST (TDD — write this before touching spotify_client.py):

File: tests/auth/test_auth_commands.py

Test cases this file must include:
- test_login_missing_client_id — TC-02: SPOTIFY_CLIENT_ID unset exits 2 with JSON on stderr
- test_get_auth_manager_creates_cache_directory — get_auth_manager() ensures cache dir exists
- test_get_auth_manager_passes_open_browser_false — open_browser=False is forwarded to SpotifyPKCE

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


def test_get_auth_manager_passes_open_browser_false(monkeypatch):
    """get_auth_manager(open_browser=False) passes the flag through to SpotifyPKCE."""
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-id")
    with patch("spotify_cli.core.spotify_client.SpotifyPKCE") as mock_pkce:
        get_auth_manager(open_browser=False)
    call_kwargs = mock_pkce.call_args.kwargs
    assert call_kwargs.get("open_browser") is False


Run the test now — it should FAIL (RED state) because spotify_client.py is still a stub:
  uv run pytest tests/auth/test_auth_commands.py -x -q --no-cov
Confirm it fails before continuing.

IMPLEMENT — replace spotify_cli/core/spotify_client.py entirely:

import os
import pathlib
import typer
import spotipy
from spotipy.oauth2 import SpotifyPKCE

CACHE_PATH = pathlib.Path.home() / ".config" / "spotify-cli" / ".cache"
SCOPES = "playlist-modify-public playlist-modify-private user-read-private"
REDIRECT_URI = "http://127.0.0.1:9090/callback"


def require_client_id() -> None:
    """Guard: exits with code 2 and structured JSON on stderr if SPOTIFY_CLIENT_ID is not set."""
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
    """
    Construct and return a SpotifyPKCE instance with CacheFileHandler.

    Creates the cache directory (~/.config/spotify-cli/) if it does not exist.
    """
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

Now update spotify_cli/auth/commands.py so the login stub calls require_client_id()
(needed for TC-02 to route through the guard):

import typer
from spotify_cli.core.spotify_client import require_client_id


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
    """
    require_client_id()
    raise NotImplementedError("Full login flow implemented in E1-S3")


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

VERIFY (must exit 0):
  uv run pytest tests/auth/test_auth_commands.py -x -q --no-cov

If the test passes, Wave 1 is complete.
```

---

### Wave 2 — Integration Verification (no code changes — report only)

```
You are running integration verification for Sprint-01. DO NOT change any code.
Your job is to run commands and report pass/fail for each check.

CHECKS TO RUN:

1. Help output check:
   uv run spotify-cli --help
   PASS if: command exits 0 AND output contains the word "Usage:"
   FAIL if: non-zero exit code or "Usage:" not in output

2. Version check:
   uv run spotify-cli --version
   PASS if: exits 0 AND output contains "0.1.0"

3. Short help flag — root:
   uv run spotify-cli -h
   PASS if: exits 0 AND output contains "Usage:"

4. Short help flag — auth group:
   uv run spotify-cli auth -h
   PASS if: exits 0 AND output contains "Usage:"

5. Short help flag — auth login command:
   uv run spotify-cli auth login -h
   PASS if: exits 0 AND output contains "Usage:"

6. Full test suite:
   uv run pytest -x -q --no-cov
   PASS if: exits 0
   FAIL if: any test fails or import errors occur

7. Package structure check (SPEC-001 §2.1 file tree):
   test -f spotify_cli/__init__.py           && echo "PASS" || echo "FAIL: spotify_cli/__init__.py"
   test -f spotify_cli/main.py               && echo "PASS" || echo "FAIL: spotify_cli/main.py"
   test -f spotify_cli/auth/__init__.py      && echo "PASS" || echo "FAIL: spotify_cli/auth/__init__.py"
   test -f spotify_cli/auth/commands.py      && echo "PASS" || echo "FAIL: spotify_cli/auth/commands.py"
   test -f spotify_cli/core/__init__.py      && echo "PASS" || echo "FAIL: spotify_cli/core/__init__.py"
   test -f spotify_cli/core/spotify_client.py && echo "PASS" || echo "FAIL: spotify_cli/core/spotify_client.py"
   test -f tests/__init__.py                 && echo "PASS" || echo "FAIL: tests/__init__.py"
   test -f tests/auth/__init__.py            && echo "PASS" || echo "FAIL: tests/auth/__init__.py"
   test -f tests/auth/test_auth_commands.py  && echo "PASS" || echo "FAIL: tests/auth/test_auth_commands.py"

8. CACHE_PATH constant check:
   uv run python -c "from spotify_cli.core.spotify_client import CACHE_PATH; \
     expected = str(__import__('pathlib').Path.home() / '.config' / 'spotify-cli' / '.cache'); \
     actual = str(CACHE_PATH); \
     print('PASS: CACHE_PATH =', actual) if actual == expected else print('FAIL: CACHE_PATH =', actual, 'expected', expected)"

After running all checks, report:
- Summary line: "Sprint-01 verification: N/8 checks passed"
- List any FAIL items with the exact command output
- Do NOT attempt to fix failures — report only and stop
```

---

## Sprint Completion Checklist

After Wave 2 verification passes, the orchestrator updates PM artifacts:

**For E1-S1:**
- Update `Project-Management/Stories/E1-S1_Project-Scaffold.md` Status field → `✅ Done`
- Check all Definition of Done checkboxes in that file

**For E1-S2:**
- Update `Project-Management/Stories/E1-S2_Spotify-Client-Factory.md` Status field → `✅ Done`
- Check all Definition of Done checkboxes in that file

**Update `Project-Management/Sprints/Sprint-01/sprint-backlog.md`:**
- Change E1-S1 Status → `✅ Done`
- Change E1-S2 Status → `✅ Done`
- Update Points Tracker Done column: Wave 0 → 2, Wave 1 → 2, Total → 4
- Append a Daily Progress row with today's date and outcomes

**Update `Project-Management/Backlog/Product-Backlog.md`:**
- E1-S1 row: Status → `✅ Done`
- E1-S2 row: Status → `✅ Done`
- EP-001 epic row: Progress → "20% (2/10pts)"

**Update `Project-Management/README.md`:**
- Current Sprint quick link → already points to `Sprints/Sprint-01/sprint-backlog.md` (no change needed)
- Current Status Sprint field → "Sprint-01 in progress" → "Sprint-01 complete — Sprint-02 next"
- Progress Summary EP-001 row → "20%"

---

## Autonomous Decision Reference

| Decision | Answer | Source |
|----------|--------|--------|
| CACHE_PATH value | `pathlib.Path.home() / ".config" / "spotify-cli" / ".cache"` → resolves to `~/.config/spotify-cli/.cache` | E1-S2 story §Technical Notes, SPEC-001 §3.2 |
| Scopes string | `"playlist-modify-public playlist-modify-private user-read-private"` (space-separated, single string) | E1-S2 story, SPEC-001 §3.2, ADR-001 §5 |
| Redirect URI | `"http://127.0.0.1:9090/callback"` — NOT `localhost` (banned by Spotify Nov 2025) | ADR-001 §1 |
| Env var name for client ID | `SPOTIFY_CLIENT_ID` | SPEC-001 §1.5 SFR-09, ADR-001 §5 |
| Exit code for missing env var | `2` — `typer.Exit(code=2)` | SPEC-001 §1.6 SNFR-03, E1-S2 AC |
| Exit code for success | `0` | SPEC-001 §1.6 SNFR-03 |
| Cache handler constructor | `spotipy.cache_handler.CacheFileHandler(cache_path=str(CACHE_PATH))` — use string, not Path | SPEC-001 §3.2, E1-S2 story |
| TC-02 test file location | `tests/auth/test_auth_commands.py` — NOT `tests/core/` | SPEC-001 §2.1, E1-S2 story |
| spotipy minimum version | `>=2.25.1` — required for CVE-2025-27154 (600-permission enforcement) | E1-S1 story §External Dependencies, ADR-001 §8 |
| typer minimum version | `>=0.12.0` | E1-S1 story §Technical Notes |
| Python minimum version | `>=3.11` | E1-S1 story §Technical Notes |
| How to emit JSON error to stderr | `typer.echo("...", err=True)` | E1-S2 story §Technical Notes note about CliRunner |
| CliRunner stderr behaviour | Typer `CliRunner` merges stderr into `.output` by default — assert on `result.output` for stderr content | E1-S2 story §Notes |
| `SPOTIFY_CLIENT_SECRET` required? | No — PKCE flow uses only `SPOTIFY_CLIENT_ID`. Do not add or check for the secret. | ADR-001 |
| pytest targeted verify command | `uv run pytest tests/auth/ -x -q --no-cov` | Sprint-01 README §DoD |
| `--version` flag wiring | `@app.callback()` with `is_eager=True` callback on `--version` option | E1-S1 story §Description, SPEC-001 §3.1 T-03 |
