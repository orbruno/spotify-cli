# Story: Batch Module

**Epic**: [E3 - Playlist Creation](../Epics/E3_Playlist-Creation.md)
**Story ID**: E3-S2
**Story Points**: 3
**Priority**: High
**Status**: To Do

## User Story

As a **developer**,
I want a **batch module that chunks track URIs into groups of 100 and POSTs them to the Spotify API**,
So that **large playlists are created reliably within Spotify's API limits**.

## Description

Implement `spotify_cli/playlist/batch.py`. The module defines the `ResolvedTrack` and `BatchResult` dataclasses shared across the playlist stack, a `chunk_uris()` generator that splits a URI list into ≤100-item groups, and a `batch_add()` function that orchestrates all chunks against `POST /playlists/{id}/items`.

A failure on one batch (including 429 rate-limit responses) does not abort subsequent batches — the failure is recorded per-track in the results array and processing continues. This ensures a single search miss or transient API error cannot silently discard the rest of the playlist.

## Acceptance Criteria

- [ ] 150 URIs produce exactly 2 API calls (100 + 50)
- [ ] A 429 response triggers a retry with `Retry-After` delay (up to 3 retries) before marking the batch as failed
- [ ] Failed tracks are included in results with a `reason` field — the entire batch is not aborted
- [ ] All results are collected before returning (no partial result on success path)
- [ ] Unit tests cover: chunking logic, partial batch failure, 429 retry behaviour

## Technical Notes

### Implementation Approach

`chunk_uris(uris, size=100)` uses a simple list slice: `[uris[i:i+size] for i in range(0, len(uris), size)]`.

`batch_add()` first separates already-failed tracks (search misses marked `status="failed"` by the resolver) from addable tracks. It then iterates over chunks of addable URIs, calls `sp.playlist_add_items()`, and catches `spotipy.SpotifyException`. Each chunk's tracks are mapped back to their `ResolvedTrack` input object for the result entry.

Retry logic for 429: check `exc.http_status == 429`, extract `Retry-After` header, sleep, and retry up to 3 times before marking the batch failed.

### Code Examples (if helpful)

```python
@dataclass
class ResolvedTrack:
    input: dict
    uri: str | None
    status: str = "pending"
    reason: str = ""

@dataclass
class BatchResult:
    playlist_id: str
    tracks_requested: int
    tracks_added: int = 0
    tracks_failed: int = 0
    results: list[dict] = field(default_factory=list)

def chunk_uris(uris: list[str], size: int = 100) -> list[list[str]]:
    return [uris[i:i + size] for i in range(0, len(uris), size)]

def batch_add(sp, playlist_id, resolved_tracks) -> BatchResult:
    ...
```

Full skeleton available in SPEC-003 §3.2.

### Files/Components Affected

- `spotify_cli/playlist/batch.py` — implement
- `tests/playlist/test_batch.py` — unit tests

### External Dependencies

- `spotipy ≥2.25.1` — `sp.playlist_add_items(playlist_id, uris)`
- `dataclasses` (stdlib)

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] Tests written and passing (`uv run pytest tests/playlist/test_batch.py`)
- [ ] Self-reviewed
- [ ] `ResolvedTrack` and `BatchResult` dataclasses importable from `playlist.batch`
- [ ] Integrated with main codebase (imported by `commands.py` and `resolver.py`)
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E3-S1 (Input Parser): `ResolvedTrack` dataclass is populated from the normalised track list

**Blocks**:
- E3-S3 (Search Resolver): imports `ResolvedTrack` from `batch.py`
- E3-S4 (Playlist Commands): calls `batch_add()` in `add_tracks` and `create_and_add`

## Related Stories

- E3-S1: Input Parser — produces the normalised track list that becomes `ResolvedTrack` inputs
- E3-S3: Search Resolver — populates `ResolvedTrack.uri` before `batch_add()` is called
- E3-S4: Playlist Commands — orchestrates resolver → batch in `add_tracks`
- E3-S5: Playlist Tests — TC-09 (150 tracks → 2 batches) lives in `test_batch.py`

## Notes

- SPEC-003 §3.2 (Phase 2) contains full implementation tasks (T-10 through T-14) and the complete code skeleton.
- Test case TC-09 (150 tracks → 2 API calls) is the primary acceptance signal for this story.
- The `ResolvedTrack` dataclass is defined here (not in resolver) because `batch.py` is the consumer — this avoids a circular import.

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
