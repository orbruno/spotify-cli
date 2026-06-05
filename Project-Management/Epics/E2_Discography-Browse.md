# Epic 2: Discography Browse

**Epic ID**: E2
**Status**: To Do
**Priority**: High
**Story Points**: 16 points
**Owner**: Orlando Bruno

## Epic Description

As an **AI agent or developer**,
I need to **fetch and stream an artist's full album and track catalogue from Spotify as NDJSON**,
So that **playlist creation can use verified Spotify URIs selected from a structured catalogue rather than guessing track names via search**.

## Goals

1. Implement `spotify-cli discography {artist_name}` — stream all tracks for an artist as NDJSON to stdout.
2. Cache per-artist results with a 24h TTL to avoid redundant API calls across repeated invocations.
3. Provide filter flags (`--album-type`, `--from-year`, `--to-year`) so agents and users can slice the catalogue.

## Success Criteria

- [ ] `spotify-cli discography "Johnny Cash"` streams NDJSON to stdout and exits 0
- [ ] Second invocation within 24h reads from cache with zero API calls
- [ ] `--no-cache` forces a fresh fetch and overwrites the cache
- [ ] `--album-type single` returns only singles; `--from-year 1960 --to-year 1970` returns only that decade
- [ ] Artist not found exits 4 with structured JSON on stderr, nothing on stdout
- [ ] Not authenticated exits 1 with structured JSON on stderr
- [ ] Cache file is always valid JSON (atomic write); partial writes never leave a corrupt file
- [ ] All tests pass: `uv run pytest tests/discography/ -v`
- [ ] 80%+ test coverage across `commands.py`, `fetcher.py`, `cache.py`

## User Stories

| ID | Story | Points | Priority | Status |
|----|-------|--------|----------|--------|
| [E2-S1](../Stories/E2-S1_Cache-Module.md) | Cache Module — file-based discography cache with 24h TTL | 3 | High | ⏳ To Do |
| [E2-S2](../Stories/E2-S2_Fetcher-Module.md) | Fetcher Module — artist lookup, album pagination, track yield generator | 5 | High | ⏳ To Do |
| [E2-S3](../Stories/E2-S3_Discography-Command.md) | Discography Command — Typer entrypoint, NDJSON streaming, structured errors | 5 | High | ⏳ To Do |
| [E2-S4](../Stories/E2-S4_Discography-Tests.md) | Discography Tests — full test suite for cache, fetcher, and command | 3 | Medium | ⏳ To Do |

**Total**: 16 story points

## Technical Approach

### Overview

Three pure Python modules — `cache.py`, `fetcher.py`, `commands.py` — inside a new `spotify_cli/discography/` package. The command checks the cache first; on miss it delegates to the fetcher, streams tracks as NDJSON, then writes the cache. Auth is handled entirely by `spotify_client.py` from SPEC-001.

### Key Components

- `cache.py`: Computes cache path (`~/.config/spotify-cli/cache/discography/{artist_id}.json`), validates TTL, reads/writes with atomic `.tmp` → rename pattern. Stdlib only (`json`, `pathlib`, `datetime`).
- `fetcher.py`: Resolves artist name → Spotify ID via `sp.search()`, paginates albums via `sp.artist_albums()` + `sp.next()`, yields flat track dicts from `sp.album_tracks()`. Generator — does not buffer all tracks in memory.
- `commands.py`: Typer command group with all flags (`--album-type`, `--from-year`, `--to-year`, `--page-all`, `--no-cache`, `--format`). Streams NDJSON to stdout; writes structured JSON errors to stderr with semantic exit codes.

### Technical Notes

- NDJSON over single JSON array: allows streaming — first track line emitted before full traversal completes.
- Cache written only after full traversal to avoid partial cache files.
- `--page-all` is opt-in; default fetches first page only (up to 50 albums) for interactive performance.
- No ANSI escape codes on stdout when piped (`sys.stdout.isatty()` check).
- Ref: [ADR-002 — Track Resolution Strategy — Discography-First over Search-First](../../_Design/03_ADR/ADR-002__track-resolution-strategy.md)

## Dependencies

**Blocks**:
- EP-003: Playlist Creation — discography output is the primary track source for playlist creation

**Depends On**:
- EP-001: Authentication & Setup — `spotify_client.py` must exist and return a valid `spotipy.Spotify` instance

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Artist with 100+ albums makes default invocation slow | Medium | `--page-all` is opt-in; default fetches first page only |
| Partial cache write corrupts future reads | High | Atomic write: `.tmp` → `rename()` on POSIX |
| Spotify 429 rate limit during large catalogues | Medium | Catch 429, sleep `Retry-After`, retry up to 3 times |
| Cache path collision for artists sharing an ID | Low | Cache keyed on Spotify artist ID (unique), not artist name |

## Acceptance Criteria (Epic-Level)

- [ ] `spotify-cli discography "Johnny Cash"` streams NDJSON lines, exits 0
- [ ] All 12 test cases (TC-01 through TC-12) from SPEC-002 pass via `uv run pytest`
- [ ] `discography` command registered in `spotify_cli/main.py` and accessible from root CLI
- [ ] Cache file at `~/.config/spotify-cli/cache/discography/{artist_id}.json` is valid JSON after any fetch

## Related Documentation

- [SPEC-002 — Discography Browse](../../_Design/04_Specs/SPEC-002__discography-browse.md)
- [ADR-002 — Track Resolution Strategy](../../_Design/03_ADR/ADR-002__track-resolution-strategy.md)
- [E1 — Authentication & Setup](./E1_Authentication-Setup.md) (dependency)
- [E3 — Playlist Creation](./E3_Playlist-Creation.md) (downstream consumer)

## Notes

This epic is the bridge between auth (EP-001) and playlist creation (EP-003). The discography-first strategy — established in ADR-002 — is what enables the AI agent to build playlists from verified URIs rather than fragile search queries. The cache layer is critical: without it, an agent calling `discography` multiple times within a session would exhaust Spotify API rate limits quickly.

---

**Created**: 2026-06-04
**Last Updated**: 2026-06-04
