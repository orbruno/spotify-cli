# Sprint 05 Backlog

**Sprint**: Sprint-05
**Date**: TBD
**Sprint Goal**: Input parser handles all three input modes (stdin/--uri/--file); batch chunks and POSTs 100 URIs at a time; resolver handles search fallback — full playlist pipeline wired, ready for commands.
**Total Points**: 8
**Status**: Planned

---

## Committed Stories

| ID | Story | Points | Status |
|----|-------|--------|--------|
| E3-S1 | Input Parser — detect & validate stdin / `--uri` / `--file` sources | 3 | To Do |
| E3-S2 | Batch Module — chunk URIs into 100-item groups and POST to Spotify | 3 | To Do |
| E3-S3 | Search Resolver — resolve tracks without URI via Spotify search | 2 | To Do |

**Total**: 8 points

---

## Task Breakdown

### E3-S1 — Input Parser (3 pts)

- [ ] Create `spotify_cli/playlist/__init__.py` (new package)
- [ ] Create `tests/playlist/__init__.py` (new test package, empty)
- [ ] Define `URI_PATTERN = re.compile(r"^spotify:track:[a-zA-Z0-9]+$")` in `spotify_cli/playlist/input_parser.py`
- [ ] Define `InputError` dataclass with fields `message: str`, `code: int`, `reason: str = ""`, `suggestion: str = ""`; implement `to_dict()` returning structured error JSON
- [ ] Implement mutual exclusivity check in `parse_track_input()`: count active input sources (`bool(uris)`, `file is not None`, `not stdin_stream.isatty()`); raise `InputError(code=2)` if count > 1 (ambiguous) or count == 0 (no input)
- [ ] Implement stdin path: parse JSON array from `stdin_stream`, normalise to `list[dict]`
- [ ] Implement `--uri` path: wrap each URI string as `{"uri": uri}`
- [ ] Implement `--file` path: reject paths containing `..` with `InputError(code=3)` (path traversal prevention); read JSON file, normalise to `list[dict]`
- [ ] Implement `_validate_uris()`: scan every item with a `uri` key; raise `InputError(code=3)` on first mismatch against `URI_PATTERN`
- [ ] Write `tests/playlist/test_input_parser.py` covering: valid JSON stdin, `--uri` flags, `--file`, multiple sources (exits 2), TTY no flags (exits 2), invalid URI format (exits 3), path traversal (exits 3)

### E3-S2 — Batch Module (3 pts)

- [ ] Define `ResolvedTrack` dataclass in `spotify_cli/playlist/batch.py`: fields `input: dict`, `uri: str | None`, `status: str = "pending"`, `reason: str = ""`
- [ ] Define `BatchResult` dataclass: fields `playlist_id: str`, `tracks_requested: int`, `tracks_added: int = 0`, `tracks_failed: int = 0`, `results: list[dict] = field(default_factory=list)`
- [ ] Implement `chunk_uris(uris: list[str], size: int = 100) -> list[list[str]]`: `[uris[i:i+size] for i in range(0, len(uris), size)]`
- [ ] Implement `batch_add(sp, playlist_id, resolved_tracks) -> BatchResult`: separate pre-failed tracks (status="failed") from addable tracks; iterate over `chunk_uris(addable_uris)` calling `sp.playlist_add_items(playlist_id, chunk)`
- [ ] Add 429 retry logic in `batch_add`: catch `SpotifyException` with `http_status == 429`, read `Retry-After` header, sleep, retry up to 3 times before marking batch as failed
- [ ] Ensure failed tracks are included in `BatchResult.results` with a `reason` field — a failure on one batch does not abort subsequent batches
- [ ] Write `tests/playlist/test_batch.py` covering: 150 URIs → 2 API calls (100+50), partial batch failure (failed tracks in results), 429 retry behaviour

### E3-S3 — Search Resolver (2 pts)

- [ ] Implement `_search_track(sp, artist, track) -> str | None` in `spotify_cli/playlist/resolver.py`: call `sp.search(q=f"artist:{artist} track:{track}", type="track", limit=1)`, return `items[0]["uri"]` if results exist, else `None`
- [ ] Implement `resolve_tracks(sp, tracks: list[dict]) -> list[ResolvedTrack]`: for each item, if `uri` present → pass through as `ResolvedTrack(status="pending")`; else → call `_search_track()`; if found → `ResolvedTrack(uri=found, status="pending")`; if not found → `ResolvedTrack(uri=None, status="failed", reason="no search match found")`
- [ ] Import `ResolvedTrack` from `playlist.batch` (avoid circular imports)
- [ ] Write `tests/playlist/test_resolver.py` covering: URI passthrough (no search call made), successful search hit, search returns empty (status="failed"), processing continues after failed resolution

---

## Acceptance Criteria Summary

**E3-S1**:
- Valid JSON stdin produces a normalised track list
- `--uri` flags produce the same normalised list as equivalent stdin input
- `--file path.json` reads the file and produces a normalised list
- Multiple input sources provided simultaneously → exits 2 with structured JSON error on stderr
- Stdin is TTY with no `--uri`/`--file` → exits 2 with structured JSON error on stderr
- Any URI not matching `spotify:track:[a-zA-Z0-9]+` → exits 3 with structured JSON error on stderr
- `--file` path containing `..` → exits 3 with structured JSON error on stderr

**E3-S2**:
- 150 URIs produce exactly 2 API calls (100 + 50)
- A 429 response triggers a retry with `Retry-After` delay (up to 3 retries) before marking batch failed
- Failed tracks are included in results with a `reason` field — batch is not aborted
- All results are collected before returning (no partial result on success path)
- Tests cover: chunking logic, partial batch failure, 429 retry behaviour

**E3-S3**:
- A track with a `uri` field bypasses search and is returned with its original URI
- A track without `uri` but with valid `artist` and `track` fields triggers a search and returns canonical URI
- A track with no `uri` and no search match → `ResolvedTrack(status="failed", reason="no search match found")`
- The rest of the playlist continues after a failed resolution (non-fatal)
- Tests cover: URI passthrough, successful search, no-match fallback

---

## Definition of Done

- [ ] All code implemented following conventions (Python, uv)
- [ ] All acceptance criteria met for E3-S1, E3-S2, and E3-S3
- [ ] `uv run pytest tests/playlist/test_input_parser.py` passes
- [ ] `uv run pytest tests/playlist/test_batch.py` passes
- [ ] `uv run pytest tests/playlist/test_resolver.py` passes
- [ ] Spotipy mocked in all tests — no live API calls
- [ ] `ResolvedTrack` and `BatchResult` importable from `spotify_cli.playlist.batch`
- [ ] `parse_track_input()` importable from `spotify_cli.playlist.input_parser`
- [ ] `resolve_tracks()` importable from `spotify_cli.playlist.resolver`
- [ ] Self-reviewed
- [ ] No known bugs or issues

---

## Risks / Notes

- Primary dependency: Sprint-02 complete (auth needed for `resolve_tracks()` API calls at runtime; tests are mocked)
- Sprint-04 recommended but not strictly required for this sprint — discography is optional input to playlist
- E3-S1, E3-S2, and E3-S3 have a soft dependency chain: E3-S2 defines `ResolvedTrack` used by E3-S3, but all three can be developed in the same session starting with E3-S1 → E3-S2 → E3-S3
- `stdin_stream` parameter defaults to `sys.stdin` but is injectable for testing without TTY concerns
- The "first result accepted" strategy in the resolver is intentional — no ranking logic; callers that need precise matching should supply URIs directly

---

**Last Updated**: 2026-06-05
**Status**: Planned
