# Story: Playlist Commands

**Epic**: [E3 - Playlist Creation](../Epics/E3_Playlist-Creation.md)
**Story ID**: E3-S4
**Story Points**: 8
**Priority**: High
**Status**: To Do

## User Story

As an **AI agent running a Claude session**,
I want to **run `spotify-cli playlist create-and-add --name "Road Trip 70s"` with a piped track list**,
So that **a fully-populated playlist appears in Spotify with zero manual steps**.

## Description

Implement `spotify_cli/playlist/commands.py` and register all three sub-commands on the root Typer app in `main.py`. The three sub-commands are:

- `playlist create --name --description --public/--private` — calls `POST /me/playlists`, returns JSON with `playlist_id`, `name`, `url`, `public`
- `playlist add-tracks {playlist_id}` — runs input parser → resolver → batch → returns full result JSON
- `playlist create-and-add --name ...` — creates playlist then adds tracks in one invocation

All write commands support `--dry-run`: for `add-tracks`, it prints the batch payload JSON and exits 0 without any POST. For `create-and-add --dry-run`, neither the create call nor any add calls are made.

This is the highest-point story in E3 (8 pts) because it integrates all three upstream modules and must handle the full error surface: auth failure (exit 1), bad input (exit 2), validation errors (exit 3), resource not found (exit 4).

## Acceptance Criteria

- [ ] `playlist create --name "Test"` returns `{"playlist_id": "...", "name": "...", "url": "...", "public": false}` and exits 0
- [ ] `playlist add-tracks {id}` with valid JSON stdin adds all tracks and returns full result JSON, exits 0
- [ ] `--dry-run` on `add-tracks` prints batch payload JSON, exits 0, and makes no API write calls
- [ ] `--dry-run` on `create-and-add` prints payload JSON, exits 0, and creates neither a playlist nor any tracks
- [ ] `create-and-add` end-to-end: creates playlist then adds tracks in a single invocation, result JSON includes both playlist metadata and track results
- [ ] Partial failure (some tracks not resolved) exits 0 with failed tracks in `results[]`
- [ ] Not authenticated exits 1 with structured JSON error on stderr
- [ ] Playlist ID not found exits 4 with structured JSON error on stderr
- [ ] All output is valid JSON; ANSI codes stripped when stdout is not a TTY
- [ ] All sub-commands reachable via `spotify-cli playlist --help`

## Technical Notes

### Implementation Approach

Register a `playlist_app = typer.Typer()` sub-app in `commands.py` and add it to the root app in `main.py` with `app.add_typer(playlist_app, name="playlist")`.

`_emit_error(error_dict, code)` writes JSON to stderr via `typer.echo(..., err=True)` and raises `typer.Exit(code=code)`.

For `add-tracks`, the call chain is: `parse_track_input()` → `resolve_tracks()` → `batch_add()`. `InputError` is caught and re-emitted with its exit code. `SpotifyException` with `http_status == 404` maps to exit 4; all other Spotify errors map to exit 1.

`--dry-run` for `add-tracks`: resolve tracks, collect URIs, print `{dry_run: true, playlist_id, tracks_to_add, batches, payload}`, exit 0. No `sp.playlist_add_items` call.

`--dry-run` for `create-and-add`: skip the `user_playlist_create` call as well. Use a placeholder `playlist_name` in the dry-run payload.

### Code Examples (if helpful)

```python
import typer, json, spotipy
from spotify_cli.core.spotify_client import get_auth_manager, require_client_id
from playlist.input_parser import parse_track_input, InputError
from playlist.resolver import resolve_tracks
from playlist.batch import batch_add

playlist_app = typer.Typer()

def _emit_error(error: dict, code: int) -> None:
    typer.echo(json.dumps(error), err=True)
    raise typer.Exit(code=code)

@playlist_app.command("create")
def create(name: str = typer.Option(..., "--name"), ...):
    ...

@playlist_app.command("add-tracks")
def add_tracks(playlist_id: str = typer.Argument(...), ...):
    ...

@playlist_app.command("create-and-add")
def create_and_add(name: str = typer.Option(..., "--name"), ...):
    ...
```

Full skeleton available in SPEC-003 §3.4.

### Files/Components Affected

- `spotify_cli/playlist/commands.py` — implement all three sub-commands
- `spotify_cli/main.py` — register `playlist_app` sub-app
- `tests/playlist/test_commands.py` — integration tests via Typer test runner

### External Dependencies

- `typer` — sub-app registration, `CliRunner` for tests
- `spotipy ≥2.25.1` — `user_playlist_create`, `playlist_add_items`, `search`
- `core/spotify_client.py` — `get_auth_manager()`, `require_client_id()` (SPEC-001)
- `playlist.input_parser` — `parse_track_input`, `InputError`
- `playlist.resolver` — `resolve_tracks`
- `playlist.batch` — `batch_add`, `chunk_uris`

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] Tests written and passing (`uv run pytest tests/playlist/test_commands.py`)
- [ ] Self-reviewed
- [ ] All JSON output validated; exit codes verified for all paths
- [ ] `--help` for all three sub-commands includes `Usage:` and `Example:` blocks
- [ ] Integrated with `main.py`; `spotify-cli playlist` is reachable
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E3-S1 (Input Parser): `parse_track_input()` called in `add_tracks` and `create_and_add`
- E3-S2 (Batch Module): `batch_add()` called after resolution
- E3-S3 (Search Resolver): `resolve_tracks()` called before batching
- EP-001 (Authentication): `get_auth_manager()` from `core/spotify_client.py`

**Blocks**:
- E3-S5 (Playlist Tests): `test_commands.py` invokes the fully registered Typer app

## Related Stories

- E3-S1: Input Parser — `parse_track_input()` is the first call in every write command
- E3-S2: Batch Module — `batch_add()` is the final step before emitting result JSON
- E3-S3: Search Resolver — `resolve_tracks()` bridges parser output to batch input
- E3-S5: Playlist Tests — TC-01, TC-02, TC-03, TC-10, TC-11, TC-13, TC-14 all exercise these commands

## Notes

- SPEC-003 §3.4 (Phase 4) contains full implementation tasks (T-18 through T-24) and the commands skeleton.
- The 8-point estimate reflects integration complexity: this story must correctly handle the full error surface of three upstream modules plus Spotipy exceptions.
- Output schemas for all three commands are specified in SPEC-003 §2.4.
- Test cases that map to this story: TC-01 (create), TC-02 (add stdin), TC-03 (dry-run), TC-10 (create-and-add), TC-11 (--file), TC-13 (not authenticated), TC-14 (404).

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
