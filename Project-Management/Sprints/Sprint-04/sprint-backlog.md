# Sprint 04 Backlog

**Sprint**: Sprint-04
**Date**: TBD
**Sprint Goal**: `spotify-cli discography 'Johnny Cash'` streams NDJSON to stdout; TC-01 through TC-11 from SPEC-002 pass.
**Total Points**: 8
**Status**: Planned

---

## Committed Stories

| ID | Story | Points | Status |
|----|-------|--------|--------|
| E2-S3 | Discography Command — Typer entrypoint, NDJSON streaming, structured errors | 5 | To Do |
| E2-S4 | Discography Tests — full test suite for cache, fetcher, and command | 3 | To Do |

**Total**: 8 points

---

## Task Breakdown

### E2-S3 — Discography Command (5 pts)

- [ ] Create `spotify_cli/discography/commands.py` with a `typer.Typer(name="discography")` app
- [ ] Define `AlbumType(str, Enum)` with values `album`, `single`, `compilation`, `all`
- [ ] Implement `emit(track: dict) -> None`: uses `sys.stdout.write(line + "\n")` + `sys.stdout.flush()` (not `print()`) for immediate streaming
- [ ] Implement `_error_exit(error, reason, suggestion, help_cmd, code)`: writes JSON to stderr via `sys.stderr.write`, raises `typer.Exit(code=code)`
- [ ] Implement `browse()` command with args: `artist_name`, `album_type`, `from_year`, `to_year`, `page_all`, `no_cache`, `fmt`
- [ ] In `browse()`, implement auth check: call `get_spotify_client()`; catch `NotAuthenticatedError` → `_error_exit(..., code=1)`
- [ ] In `browse()`, implement artist resolution: call `resolve_artist()`; catch `ArtistNotFoundError` → `_error_exit(..., code=4)`
- [ ] In `browse()`, implement cache check: if not `no_cache` and `cache.is_valid(artist["id"])` → read from cache; else fetch, collect all tracks into list, write cache, then stream
- [ ] In `browse()`, implement streaming: iterate `tracks` list, call `emit(track)` for each
- [ ] Register `discography_app` in `spotify_cli/main.py`: `app.add_typer(discography_app)`
- [ ] Verify `uv run spotify-cli discography "Johnny Cash"` streams NDJSON to terminal, exits 0 (manual test)
- [ ] Verify `spotify-cli discography` appears in `spotify-cli --help` output

### E2-S4 — Discography Tests (3 pts)

- [ ] Finalize `tests/discography/test_cache.py` with all cache scenarios (may have been started in Sprint-03 — verify and complete): cache miss, write→read roundtrip, TTL expired, atomic write, corrupt JSON as miss, `clear()`
- [ ] Finalize `tests/discography/test_fetcher.py`: `resolve_artist` success and `ArtistNotFoundError`, `fetch_albums` pagination (`page_all=True`), `apply_year_filter` exclusions, `iter_tracks` is a generator
- [ ] Create `tests/discography/test_commands.py` and implement TC-01 through TC-12 from SPEC-002:
  - TC-01: valid artist, cache miss → fetch + stream + cache write, exits 0
  - TC-02: valid artist, cache hit (within TTL) → reads cache, zero API calls, exits 0
  - TC-03: `--no-cache` → skips cache read, fetches fresh, overwrites cache, exits 0
  - TC-04: artist not found → stderr JSON `error: artist not found`, exits 4
  - TC-05: `--from-year 1960 --to-year 1970` → only tracks from that decade
  - TC-06: `--album-type single` → only singles in output
  - TC-07: not authenticated → stderr JSON `error: not authenticated`, exits 1
  - TC-08: cache expired (>24h) → treated as miss, fetch fresh, exits 0
  - TC-09: `--page-all` on artist with 60+ albums → streams all tracks
  - TC-10: `--album-type invalid-value` → stderr JSON `error: validation error`, exits 3
  - TC-11: cache file corrupt (invalid JSON) → cache miss, fetches fresh
  - TC-12: stdout piped (not TTY) → valid NDJSON, no ANSI codes
- [ ] Run coverage gate: `uv run pytest tests/discography/ --cov=spotify_cli/discography --cov-report=term-missing`
- [ ] Verify coverage ≥80% for `commands.py`, `fetcher.py`, and `cache.py`

---

## Acceptance Criteria Summary

**E2-S3**:
- `discography "Johnny Cash"` streams NDJSON to stdout, exits 0
- Each stdout line is a valid, parseable JSON object matching the output schema
- Cache hit → no API calls made, same output as fresh fetch
- `--no-cache` → bypasses cache read, fetches fresh, overwrites cache
- Artist not found → structured JSON on stderr (`error: artist not found`), exits 4, stdout empty
- Not authenticated → structured JSON on stderr (`error: not authenticated`), exits 1, stdout empty
- ANSI codes absent from stdout when piped (non-TTY context)
- `--from-year 1960 --to-year 1970` returns only tracks from albums in that decade
- `--album-type invalid-value` → structured JSON on stderr (`error: validation error`), exits 3
- Command accessible as `spotify-cli discography` after registration in `main.py`

**E2-S4**:
- All TC-01 through TC-11 from SPEC-002 pass via `uv run pytest tests/discography/ -v`
- Cache TTL expiry tested with mocked `datetime.now()` (no real-time waiting)
- Spotipy fully mocked — no live API calls in any test
- Coverage ≥80% for all discography modules
- Invalid `--album-type` value — exit 3 tested (TC-10)
- Corrupt cache treated as miss — tested (TC-11)

---

## Definition of Done

- [ ] All code implemented following conventions (Python, Typer, uv)
- [ ] All acceptance criteria met for E2-S3 and E2-S4
- [ ] All TC-01 through TC-11 (12 test cases) passing: `uv run pytest tests/discography/ -v`
- [ ] Coverage ≥80%: `uv run pytest tests/discography/ --cov=spotify_cli/discography --cov-report=term-missing`
- [ ] `spotify-cli discography "Johnny Cash"` streams NDJSON to terminal (manual verify)
- [ ] `spotify-cli discography` listed in `spotify-cli --help` (manual verify)
- [ ] Self-reviewed
- [ ] No known bugs or issues

---

## Risks / Notes

- Dependency: Sprint-03 must be complete — E2-S3 imports `cache.py` and `fetcher.py` directly
- `emit()` must use `sys.stdout.write()` + `sys.stdout.flush()`, not `print()` — `print()` buffers by default in some environments
- Cache is written after all tracks are collected (not incrementally) to guarantee the cache file is always complete
- `CliRunner` from Typer captures stdout and stderr in `result.output` (merged by default) — use `mix_stderr=False` on `CliRunner()` if assertions need separate stderr
- E2-S4 note: TC counts in the SPEC-002 reference mention TC-01–TC-11 (story file says "TC-01 through TC-12" but only 11 scenarios are listed in the test matrix) — treat TC-12 (NDJSON no ANSI) as included

---

**Last Updated**: 2026-06-05
**Status**: Planned
