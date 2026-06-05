# Sprint 03 Backlog

**Sprint**: Sprint-03
**Date**: TBD
**Sprint Goal**: Discography cache module handles miss/hit/TTL/corruption; fetcher paginates all albums and streams tracks as a generator.
**Total Points**: 8
**Status**: Planned

---

## Committed Stories

| ID | Story | Points | Status |
|----|-------|--------|--------|
| E2-S1 | Cache Module — file-based discography cache with 24h TTL | 3 | To Do |
| E2-S2 | Fetcher Module — artist lookup, album pagination, track yield generator | 5 | To Do |

**Total**: 8 points

---

## Task Breakdown

### E2-S1 — Cache Module (3 pts)

- [ ] Create `spotify_cli/discography/__init__.py` (new package)
- [ ] Create `tests/discography/__init__.py` (new test package, empty)
- [ ] Implement `CACHE_DIR = Path.home() / ".config" / "spotify-cli" / "cache" / "discography"` and `TTL_SECONDS = 86400` as module-level constants in `spotify_cli/discography/cache.py`
- [ ] Implement `cache_path(artist_id: str) -> Path` helper
- [ ] Implement `is_valid(artist_id: str) -> bool`: returns False if file missing; parses `cached_at`, computes age in seconds, returns False if age ≥ TTL; catches `KeyError`, `ValueError`, `JSONDecodeError` and returns False (never raises)
- [ ] Implement `read(artist_id: str) -> list[dict]`: returns `data.get("tracks", [])` on success; returns `[]` on `JSONDecodeError` or `OSError`
- [ ] Implement `write(artist_id, artist_name, tracks)`: atomic write via `.tmp` file then `rename()` — never writes partial data
- [ ] Implement `clear()`: removes all `.json` files in `CACHE_DIR` using `missing_ok=True`
- [ ] Write `tests/discography/test_cache.py` covering: cache miss (no file), write→read roundtrip, TTL expired, corrupt JSON treated as miss, atomic write verified (no `.tmp` file after write), `clear()` removes all files

### E2-S2 — Fetcher Module (5 pts)

- [ ] Implement `ArtistNotFoundError(Exception)` with `name` attribute in `spotify_cli/discography/fetcher.py`
- [ ] Implement `resolve_artist(sp, name) -> dict`: search for artist, return `{"id": ..., "name": ...}`, raise `ArtistNotFoundError` if result set is empty
- [ ] Implement `fetch_albums(sp, artist_id, album_type="album", page_all=False) -> list[dict]`: paginate through all pages when `page_all=True`; map `album_type="all"` to `"album,single,compilation,appears_on"`
- [ ] Implement `apply_year_filter(albums, from_year, to_year) -> list[dict]`: slice `release_date[:4]` for year extraction (handles `YYYY`, `YYYY-MM`, `YYYY-MM-DD` formats)
- [ ] Implement `iter_tracks(sp, albums, artist_name) -> Generator[dict, None, None]`: yield one track dict per iteration with fields `uri`, `name`, `artist`, `album`, `release_date`, `track_number`, `duration_ms`, `explicit`; paginate album track pages
- [ ] Add 429 rate limit retry logic around `sp.artist_albums()` and `sp.album_tracks()`: catch `SpotifyException` with HTTP 429, read `Retry-After` header (default 1s if absent), sleep, retry up to 3 times before raising
- [ ] Write `tests/discography/test_fetcher.py` covering: `resolve_artist` success, `ArtistNotFoundError` raised, `fetch_albums` paginates with `page_all=True`, `apply_year_filter` excludes out-of-range, `iter_tracks` is a generator (not a list)

---

## Acceptance Criteria Summary

**E2-S1**:
- Cache miss — `is_valid()` returns False when file does not exist
- After `write()` — `is_valid()` returns True and `read()` returns the same tracks list
- TTL expired (>24h since `cached_at`) — `is_valid()` returns False
- Atomic write — data written to `.tmp` file then renamed to final path; no partial file visible
- Corrupt JSON cache file — `is_valid()` returns False (treated as miss, not exception); `read()` returns `[]`
- `clear()` removes all files in `~/.config/spotify-cli/cache/discography/`
- All scenarios covered by unit tests

**E2-S2**:
- `resolve_artist(sp, name)` returns `{id, name}` for a valid artist name
- Artist not found → `ArtistNotFoundError` raised
- `fetch_albums()` paginates through all pages when `page_all=True`
- `--from-year` / `--to-year` filters applied correctly; albums outside range excluded
- `--album-type single` returns only singles
- `iter_tracks()` is a generator — does not load all tracks into memory before yielding the first
- HTTP 429 triggers sleep using `Retry-After` header, retried up to 3 times before raising

---

## Definition of Done

- [ ] All code implemented following conventions (Python, uv)
- [ ] All acceptance criteria met for E2-S1 and E2-S2
- [ ] `uv run pytest tests/discography/test_cache.py -v` passes
- [ ] `uv run pytest tests/discography/test_fetcher.py -v` passes
- [ ] Spotipy fully mocked — no live API calls in tests
- [ ] Use `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)` in cache tests to avoid touching real home directory
- [ ] Self-reviewed
- [ ] No known bugs or issues

---

## Risks / Notes

- Dependency: Sprint-02 must be complete — auth is needed for live API calls (tests are mocked, but E2-S3 will need `get_spotify_client()` which depends on E1)
- E2-S1 and E2-S2 can be worked in any order within this sprint — they don't depend on each other
- Use `monkeypatch.setattr` not `monkeypatch.setattr(cache_mod, "cache_path", ...)` — redirect `CACHE_DIR` at module level so all path operations derive from it consistently
- TC-08 (TTL expiry) in E2-S4 does not require `time.sleep` — monkeypatch `datetime.now` to return a time 25 hours in the past
- `release_date` from Spotify can be `"YYYY"`, `"YYYY-MM"`, or `"YYYY-MM-DD"` — `apply_year_filter` must handle all three via `[:4]` slice

---

**Last Updated**: 2026-06-05
**Status**: Planned
