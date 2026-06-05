# Sprint 06 Backlog

**Sprint**: Sprint-06
**Date**: TBD
**Sprint Goal**: `spotify-cli playlist create-and-add` works end-to-end; `--dry-run` returns payload without writing; TC-01 through TC-12 from SPEC-003 pass; CLI is ready for agent use.
**Total Points**: 11
**Status**: Planned

---

## Committed Stories

| ID | Story | Points | Status |
|----|-------|--------|--------|
| E3-S4 | Playlist Commands — `create`, `add-tracks`, `create-and-add` Typer commands | 8 | To Do |
| E3-S5 | Playlist Tests — full test suite covering all input modes and error paths | 3 | To Do |

**Total**: 11 points

---

## Task Breakdown

### E3-S4 — Playlist Commands (8 pts)

- [ ] Create `spotify_cli/playlist/commands.py` with `playlist_app = typer.Typer()` sub-app
- [ ] Implement `_emit_error(error: dict, code: int)`: writes JSON to stderr via `typer.echo(..., err=True)` and raises `typer.Exit(code=code)`
- [ ] Implement `playlist create` command: args `--name`, `--description`, `--public/--private`; call `sp.current_user()` for user ID; call `sp.user_playlist_create(user_id, name, public=public, description=description)`; return `{"playlist_id": ..., "name": ..., "url": ..., "public": ...}`, exit 0
- [ ] Implement `playlist add-tracks {playlist_id}` command: call chain `parse_track_input()` → `resolve_tracks()` → `batch_add()`; catch `InputError` and re-emit with its exit code; catch `SpotifyException` with `http_status == 404` → exit 4; all other Spotify errors → exit 1; return full result JSON, exit 0
- [ ] Implement `--dry-run` for `add-tracks`: resolve tracks, collect URIs, print `{dry_run: true, playlist_id, tracks_to_add, batches, payload}`, exit 0 — no `sp.playlist_add_items()` call
- [ ] Implement `playlist create-and-add` command: `--name`, `--description`, `--public/--private`, plus all `add-tracks` input flags; creates playlist then adds tracks; result JSON includes both playlist metadata and track results
- [ ] Implement `--dry-run` for `create-and-add`: skip `user_playlist_create` call as well; use placeholder playlist name in payload; print dry-run payload, exit 0 — neither create nor add calls made
- [ ] Register `playlist_app` in `spotify_cli/main.py`: `app.add_typer(playlist_app, name="playlist")`
- [ ] Verify `spotify-cli playlist --help` lists all three sub-commands (manual test)
- [ ] Verify `spotify-cli playlist create-and-add --name "Test" < tracks.json` creates playlist and adds tracks end-to-end (manual test with real Spotify credentials)
- [ ] Add `Usage:` and `Example:` blocks to `--help` for all three sub-commands
- [ ] Write `SKILL.md` (NFR-16): document how an agent uses this CLI, covering all three commands with examples
- [ ] Perform agent smoke test (NFR-17): Claude drives CLI using only `SKILL.md` + `--help` output

### E3-S5 — Playlist Tests (3 pts)

- [ ] Finalize `tests/playlist/test_input_parser.py` (may be started in Sprint-05): all input modes, URI validation, path traversal, mutual exclusion — TC-06, TC-07, TC-08, TC-12
- [ ] Finalize `tests/playlist/test_batch.py`: chunking (150 → 2 calls), 429 retry, partial failure — TC-09
- [ ] Finalize `tests/playlist/test_resolver.py`: URI passthrough, search hit, search miss — TC-04, TC-05
- [ ] Create `tests/playlist/test_commands.py` with shared `mock_sp` fixture and all TC-01 through TC-14:
  - TC-01: `test_create` — `playlist create --name "Test"` returns playlist JSON, exits 0
  - TC-02: `test_add_tracks_stdin` — valid JSON stdin adds all tracks, returns full result JSON, exits 0
  - TC-03: `test_add_tracks_dry_run` — `--dry-run` prints payload, exits 0, no API write calls
  - TC-04: `test_search_hit` — (in test_resolver.py) track without URI resolved via search
  - TC-05: `test_search_miss` — (in test_resolver.py) unresolvable track marked failed, processing continues
  - TC-06: `test_invalid_uri_format` — (in test_input_parser.py) bad URI → exits 3
  - TC-07: `test_ambiguous_input_sources` — multiple sources → exits 2
  - TC-08: `test_tty_no_flags` — TTY with no input source → exits 2
  - TC-09: `test_150_tracks_two_batches` — (in test_batch.py) 150 URIs → 2 API calls
  - TC-10: `test_create_and_add` — end-to-end create then add tracks, result includes playlist metadata and track results
  - TC-11: `test_add_tracks_file` — `--file` input mode works correctly
  - TC-12: `test_path_traversal` — (in test_input_parser.py) `--file` with `..` → exits 3
  - TC-13: `test_not_authenticated` — exits 1 with structured JSON error on stderr
  - TC-14: `test_playlist_not_found` — `SpotifyException(http_status=404)` → exits 4
- [ ] Run coverage gate: `uv run pytest tests/playlist/ --cov=spotify_cli/playlist --cov-fail-under=80`
- [ ] Verify no live Spotipy calls (assert `mock_sp.search.call_count` etc. in tests)

---

## Acceptance Criteria Summary

**E3-S4**:
- `playlist create --name "Test"` returns `{"playlist_id": "...", "name": "...", "url": "...", "public": false}`, exits 0
- `playlist add-tracks {id}` with valid JSON stdin adds all tracks and returns full result JSON, exits 0
- `--dry-run` on `add-tracks` prints batch payload JSON, exits 0, no API write calls
- `--dry-run` on `create-and-add` prints payload JSON, exits 0, creates neither playlist nor tracks
- `create-and-add` end-to-end: creates playlist then adds tracks; result JSON includes both playlist metadata and track results
- Partial failure (some tracks not resolved) exits 0 with failed tracks in `results[]`
- Not authenticated → exits 1 with structured JSON error on stderr
- Playlist ID not found → exits 4 with structured JSON error on stderr
- All output is valid JSON; ANSI codes stripped when stdout is not a TTY
- All sub-commands reachable via `spotify-cli playlist --help`

**E3-S5**:
- `uv run pytest tests/playlist/test_input_parser.py` passes
- `uv run pytest tests/playlist/test_batch.py` passes
- `uv run pytest tests/playlist/test_resolver.py` passes
- `uv run pytest tests/playlist/test_commands.py` passes (TC-01 through TC-14)
- All 12+ named test cases implemented and passing
- Spotipy mocked in all tests — no live API calls
- `uv run pytest tests/playlist/ --cov=spotify_cli/playlist --cov-fail-under=80` passes

---

## Definition of Done

- [ ] All code implemented following conventions (Python, Typer, uv)
- [ ] All acceptance criteria met for E3-S4 and E3-S5
- [ ] All 14 test cases (TC-01 through TC-14) passing: `uv run pytest tests/playlist/ -v`
- [ ] Coverage ≥80% across all four `playlist/` modules
- [ ] `uv run pytest` green across all modules (`tests/auth/`, `tests/discography/`, `tests/playlist/`)
- [ ] `spotify-cli auth login` → `discography` → `playlist create-and-add` works end-to-end (manual)
- [ ] `SKILL.md` written (NFR-16)
- [ ] Agent smoke test passed (NFR-17): Claude drives CLI using only `SKILL.md` + `--help`
- [ ] Self-reviewed
- [ ] No known bugs or issues

---

## Risks / Notes

- Dependency: Sprint-05 must be complete — E3-S4 imports `parse_track_input`, `resolve_tracks`, and `batch_add` from Sprint-05 modules
- At 11 points, this is the heaviest sprint — may need two sessions; if so, prioritise E3-S4 implementation first, then E3-S5 in session 2
- Suggested split if two sessions needed: Session A — E3-S4 command implementation + manual smoke test; Session B — E3-S5 full test suite + coverage gate + SKILL.md
- Use `typer.testing.CliRunner(mix_stderr=False)` for command integration tests to capture stdout and stderr separately
- `test_commands.py` shared `mock_sp` fixture must cover: `current_user()`, `user_playlist_create()`, `playlist_add_items()`, `search()` — use `MagicMock` for all
- NFR-16 (`SKILL.md`) and NFR-17 (agent smoke test) are project-level completion gates — do not mark sprint done without them

---

**Last Updated**: 2026-06-05
**Status**: Planned
