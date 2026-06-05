# Story: Search Resolver

**Epic**: [E3 - Playlist Creation](../Epics/E3_Playlist-Creation.md)
**Story ID**: E3-S3
**Story Points**: 2
**Priority**: High
**Status**: To Do

## User Story

As an **AI agent**,
I want the **CLI to resolve tracks that have no URI using Spotify search**,
So that **I can mix verified URIs with artist+track name pairs in a single input without pre-resolving every track**.

## Description

Implement `spotify_cli/playlist/resolver.py`. For each track in the normalised input list, the resolver checks whether a `uri` field is present. If it is, the track passes through as-is. If not, the resolver calls `GET /search?q=artist:{artist} track:{track}&type=track&limit=1` and accepts the first returned result without scoring. If the result set is empty, the track is marked `status="failed"` with `reason="no search match found"` and processing continues — the failure is not fatal.

All tracks are resolved before batching (pre-flight resolution step), so `batch_add()` receives a complete list of `ResolvedTrack` objects, some of which may already be marked failed.

## Acceptance Criteria

- [ ] A track with a `uri` field bypasses search and is returned with its original URI
- [ ] A track without a `uri` but with valid `artist` and `track` fields triggers a search and returns the canonical URI from the top result
- [ ] A track with no `uri` and no search match is returned as `ResolvedTrack(status="failed", reason="no search match found")`
- [ ] The rest of the playlist continues after a failed resolution (non-fatal)
- [ ] Unit tests cover: URI passthrough, successful search, no-match fallback

## Technical Notes

### Implementation Approach

`resolve_tracks(sp, tracks)` iterates over the normalised track list. URI passthrough: `ResolvedTrack(input=item, uri=uri, status="pending")`. Search path: call `_search_track(sp, artist, track_name)` which calls `sp.search(q=f"artist:{artist} track:{track}", type="track", limit=1)` and returns `items[0]["uri"]` or `None`.

The "first result accepted" strategy is intentional — ranking logic would add complexity without a clear quality threshold. Callers that need precise matching should supply URIs directly.

### Code Examples (if helpful)

```python
from playlist.batch import ResolvedTrack

def resolve_tracks(sp, tracks: list[dict]) -> list[ResolvedTrack]:
    resolved = []
    for item in tracks:
        uri = item.get("uri")
        if uri:
            resolved.append(ResolvedTrack(input=item, uri=uri, status="pending"))
        else:
            artist = item.get("artist", "")
            track_name = item.get("track", "")
            found_uri = _search_track(sp, artist, track_name)
            if found_uri:
                resolved.append(ResolvedTrack(input=item, uri=found_uri, status="pending"))
            else:
                resolved.append(ResolvedTrack(
                    input=item, uri=None, status="failed",
                    reason="no search match found",
                ))
    return resolved

def _search_track(sp, artist: str, track: str) -> str | None:
    results = sp.search(q=f"artist:{artist} track:{track}", type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    return items[0]["uri"] if items else None
```

Full skeleton available in SPEC-003 §3.3.

### Files/Components Affected

- `spotify_cli/playlist/resolver.py` — implement
- `tests/playlist/test_resolver.py` — unit tests

### External Dependencies

- `spotipy ≥2.25.1` — `sp.search(q, type, limit)`
- `playlist.batch.ResolvedTrack` — imported from E3-S2

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] Tests written and passing (`uv run pytest tests/playlist/test_resolver.py`)
- [ ] Self-reviewed
- [ ] Spotipy mocked in tests — no live API calls
- [ ] Integrated with main codebase (called by `commands.py` before `batch_add()`)
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E3-S2 (Batch Module): imports `ResolvedTrack` dataclass from `playlist.batch`

**Blocks**:
- E3-S4 (Playlist Commands): `add_tracks` and `create_and_add` call `resolve_tracks()` before `batch_add()`

## Related Stories

- E3-S1: Input Parser — produces the normalised track list that `resolve_tracks()` iterates over
- E3-S2: Batch Module — defines `ResolvedTrack`; receives the output of this resolver
- E3-S4: Playlist Commands — wires resolver into the full `add_tracks` flow
- E3-S5: Playlist Tests — TC-04 (search found) and TC-05 (search empty) live in `test_resolver.py`

## Notes

- SPEC-003 §3.3 (Phase 3) contains full implementation tasks (T-15 through T-17) and the complete code skeleton.
- Test cases that map to this story: TC-04 (search match found), TC-05 (search returns empty).
- E3-S2 and E3-S3 can be developed in parallel once E3-S1 is done, since they share only the `ResolvedTrack` dataclass (defined in batch.py).

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
