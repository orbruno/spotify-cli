# Story: Project Scaffold

**Epic**: [E1 - Authentication & Setup](../Epics/E1_Authentication-Setup.md)
**Story ID**: E1-S1
**Story Points**: 2
**Priority**: High
**Status**: ✅ Done

## User Story

As a **developer**,
I want to **have a properly structured Python project with pyproject.toml and a Typer app entry point**,
So that **I have a working foundation to build CLI commands on**.

## Description

Create the `spotify-cli` Python package from scratch using `uv`. The project requires a `pyproject.toml` declaring all runtime and dev dependencies, a `[project.scripts]` entry point, and a minimal package hierarchy matching the file tree defined in SPEC-001 §2.1. The root Typer app must register the `auth` sub-app and expose `--version` and `--help` / `-h`. No auth logic is implemented here — only the skeleton that makes `uv run spotify-cli --help` work.

## Acceptance Criteria

- [ ] `uv run spotify-cli --help` outputs a `Usage:` block and exits 0
- [ ] `uv run spotify-cli --version` prints the version string and exits 0
- [ ] `-h` is equivalent to `--help` at all levels
- [ ] `uv run pytest` runs without import errors (even with no test content yet)
- [ ] Package structure matches SPEC-001 §2.1 file tree exactly

## Technical Notes

### Implementation Approach

1. Create `pyproject.toml` with `uv` — set `name="spotify-cli"`, dependencies `spotipy>=2.25.1` and `typer>=0.12.0`; add dev deps `pytest>=8.0` and `pytest-cov>=5.0`; set entry point `spotify-cli = "spotify_cli.main:app"`
2. Create package skeleton with empty `__init__.py` files: `spotify_cli/__init__.py`, `spotify_cli/auth/__init__.py`, `spotify_cli/core/__init__.py`, `tests/__init__.py`, `tests/auth/__init__.py`
3. Create stub files so imports resolve: `spotify_cli/auth/commands.py`, `spotify_cli/core/spotify_client.py`
4. Implement root app in `main.py`: `app = typer.Typer(...)`, `auth_app = typer.Typer(...)`, register `auth` sub-app, wire `login` / `status` / `logout` from `auth/commands.py`, add `--version` callback
5. Verify `uv run spotify-cli --help` prints usage with version in ≤500ms (SNFR-04)

### Code Examples (if helpful)

```toml
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
```

```python
# spotify_cli/main.py
import typer
from spotify_cli.auth import commands as auth_commands

app = typer.Typer(help="Spotify CLI — manage your Spotify account from the terminal.")
auth_app = typer.Typer(help="Authentication commands.")
app.add_typer(auth_app, name="auth")

auth_app.command("login")(auth_commands.login)
auth_app.command("status")(auth_commands.status)
auth_app.command("logout")(auth_commands.logout)

if __name__ == "__main__":
    app()
```

### Files/Components Affected

- `pyproject.toml` — new
- `spotify_cli/__init__.py` — new
- `spotify_cli/main.py` — new
- `spotify_cli/auth/__init__.py` — new
- `spotify_cli/auth/commands.py` — stub (new)
- `spotify_cli/core/__init__.py` — new
- `spotify_cli/core/spotify_client.py` — stub (new)
- `tests/__init__.py` — new
- `tests/auth/__init__.py` — new

### External Dependencies

- `typer>=0.12.0` — CLI framework, auto-generates `--help`
- `spotipy>=2.25.1` — declared here; implemented in E1-S2
- `uv` — package manager and test runner

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] `uv run pytest` passes (no import errors)
- [ ] Self-reviewed
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- None — first story in the epic

**Blocks**:
- E1-S2: Spotify Client Factory — requires the package structure to exist
- E1-S3: Auth Login Command — requires `main.py` entry point
- E1-S4: Auth Status & Logout + Tests — requires full package skeleton for imports

## Related Stories

- E1-S2: Spotify Client Factory — implements `core/spotify_client.py` stub created here
- E1-S3: Auth Login Command — implements `auth/commands.py` stub created here

## Notes

- `--version` (NFR-12) is included here as a root-level concern, not a separate story
- Do not implement any auth logic in this story — stubs only; auth commands are filled in E1-S2 and E1-S3
- Phase 1 of SPEC-001 §3.1 maps directly to the tasks in this story (T-01 through T-04)

---

**Created**: 2026-06-04
**Status**: ✅ Done — 2026-06-05
