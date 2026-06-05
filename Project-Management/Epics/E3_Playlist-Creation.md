# Epic 3: Playlist Creation

**Epic ID**: E3
**Status**: To Do
**Priority**: High
**Story Points**: 19 points
**Owner**: Orlando Bruno

## Epic Description

As an **AI agent or user**,
I need to **create and populate a Spotify playlist from a structured track list in a single CLI invocation**,
So that **I can go from an LLM-generated track list to a saved Spotify playlist with zero manual steps**.

## Goals

1. Accept a JSON track list from an AI agent via stdin (or `--uri` flags / `--file`), enforce mutual exclusivity of input modes, and validate all track URIs before any write.
2. Resolve tracks that have no URI through a Spotify search fallback so that partial metadata (artist + track name) is enough to build a complete playlist.
3. Batch-add resolved URIs to Spotify in groups of 100 and return a structured JSON result containing per-track status — enabling automated reporting of which tracks were added and which failed.

## Success Criteria

- [ ] `spotify-cli playlist create --name "Test"` creates a real playlist and returns JSON with `playlist_id` and `url`, exits 0
- [ ] `spotify-cli playlist add-tracks {id}` with valid JSON stdin adds all tracks and returns results JSON, exits 0
- [ ] `spotify-cli playlist add-tracks {id} --dry-run` prints payload JSON and exits 0 without any POST to the Spotify API
- [ ] Tracks without `uri` are resolved via search; failed resolutions appear in `results` with `status: "failed"` — processing continues
- [ ] 150 tracks produce exactly 2 API batch calls (100 + 50)
- [ ] Invalid URI format exits 3 with structured JSON on stderr
- [ ] Multiple input sources simultaneously exits 2 with structured JSON on stderr
- [ ] Stdin-is-TTY with no `--uri`/`--file` exits 2 with structured JSON on stderr
- [ ] `spotify-cli playlist create-and-add` completes the full create + add flow in one invocation
- [ ] `uv run pytest tests/playlist/` passes with ≥80% coverage

## User Stories

| ID | Story | Points | Priority | Status |
|----|-------|--------|----------|--------|
| [E3-S1](../Stories/E3-S1_Input-Parser.md) | Input Parser — detect & validate stdin / `--uri` / `--file` sources | 3 | High | To Do |
| [E3-S2](../Stories/E3-S2_Batch-Module.md) | Batch Module — chunk URIs into 100-item groups and POST to Spotify | 3 | High | To Do |
| [E3-S3](../Stories/E3-S3_Search-Resolver.md) | Search Resolver — resolve tracks without URI via Spotify search | 2 | High | To Do |
| [E3-S4](../Stories/E3-S4_Playlist-Commands.md) | Playlist Commands — `create`, `add-tracks`, `create-and-add` Typer commands | 8 | High | To Do |
| [E3-S5](../Stories/E3-S5_Playlist-Tests.md) | Playlist Tests — full test suite covering all input modes and error paths | 3 | Medium | To Do |

**Total**: 19 story points

## Technical Approach

### Overview

The `playlist` command group is built as four cooperating modules under `spotify_cli/playlist/`: `input_parser.py` handles source detection and validation, `resolver.py` performs the search fallback, `batch.py` chunks and posts to the API, and `commands.py` wires them together as Typer sub-commands. Authentication is delegated entirely to `core/spotify_client.py` from SPEC-001 — no new auth logic is introduced.

### Key Components

- `input_parser.py`: Detects active input source (stdin / `--uri` / `--file`), enforces mutual exclusivity, validates URI format (`spotify:track:[a-zA-Z0-9]+`), rejects path traversal in `--file`, returns normalized `list[dict]`
- `resolver.py`: Passes through tracks with a `uri`; calls `GET /search?q=artist:X track:Y&type=track&limit=1` for tracks without one; marks unmatched tracks `failed` without aborting
- `batch.py`: Slices resolved URI list into ≤100-item chunks; POSTs each chunk to `POST /playlists/{id}/items`; collects per-track `added`/`failed` status into a `BatchResult` dataclass
- `commands.py`: Typer sub-commands `create`, `add-tracks`, `create-and-add` with `--dry-run` support; structured JSON to stdout, structured error JSON to stderr; semantic exit codes 0/1/2/3/4

### Technical Notes

- Mutual exclusivity of input modes is enforced in `parse_track_input()`, not in Typer, to keep validation logic testable in isolation.
- `--dry-run` on `create-and-add` skips both the playlist creation call and all track add calls — no Spotify resource is created.
- Batch size is fixed at 100 (Spotify API hard limit). Partial batch failure is non-fatal: failed tracks are recorded and the remaining batches continue.
- All output goes to stdout as JSON. All errors go to stderr as structured JSON with the anatomy: `{error, reason, suggestion, help}`.
- ANSI codes are stripped from stdout when output is not a TTY.

## Dependencies

**Blocks**:
- Nothing — E3 is the terminal epic in the current roadmap.

**Depends On**:
- EP-001 (Authentication & Setup) — `core/spotify_client.py` must be complete; all playlist commands require a valid auth token.

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Spotify search returns wrong top-1 match for ambiguous artist/track names | Medium | Document that callers should supply URIs for precise control; first-result strategy is intentional per ADR-003 |
| Spotipy 429 rate limit during large batch | Medium | `batch.py` catches `SpotifyException`; per-batch retry with `Retry-After` backoff (max 3 retries) |
| `--file` path validation missed edge case | Low | Reject any path whose `parts` contain `..`; unit tests cover TC-12 explicitly |

## Acceptance Criteria (Epic-Level)

- [ ] All three sub-commands (`create`, `add-tracks`, `create-and-add`) are registered and reachable via `spotify-cli playlist`
- [ ] End-to-end `create-and-add` flow works with both URI-only and name-only track inputs in the same payload
- [ ] `--dry-run` on every write command exits 0 with JSON payload and makes zero Spotify API write calls
- [ ] All 12 test cases TC-01 through TC-12 pass via `uv run pytest tests/playlist/`
- [ ] Coverage ≥80% across all four modules in `spotify_cli/playlist/`

## Related Documentation

- [SPEC-003 — Playlist Create](_Design/04_Specs/SPEC-003__playlist-create.md)
- [ADR-003 — Track List Input Contract — JSON stdin for Agent Invocation](_Design/03_ADR/ADR-003__sys__track-list-input-contract.md)
- [EP-001 — Authentication & Setup](E1_Authentication-Setup.md)

## Notes

- Stories are ordered by implementation dependency: E3-S1 (parser) → E3-S2 (batch) → E3-S3 (resolver) → E3-S4 (commands) → E3-S5 (tests). E3-S2 and E3-S3 can proceed in parallel once E3-S1 is done.
- SPEC-003 contains full code skeletons for all four modules — implementors should read the spec before starting E3-S4.
- Playlist editing (track removal, reordering) is out of scope for this epic.

---

**Created**: 2026-06-04
**Last Updated**: 2026-06-04
