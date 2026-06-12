# Story: Fetcher Module

**Epic**: [E2 - Discography Browse](../Epics/E2_Discography-Browse.md)
**Story ID**: E2-S2
**Story Points**: 5
**Priority**: High
**Status**: ✅ Done

## User Story

As a **developer**,
I want a **fetcher module that traverses an artist's full discography via the Spotify API**,
So that **the discography command has a clean, testable data layer decoupled from CLI concerns**.

## Description

Create `spotify_cli/discography/fetcher.py` — a pure Python module that handles all Spotify API interaction for the discography feature. It resolves an artist name to a Spotify ID, paginates through albums, applies year and type filters, and yields flat track dicts as a generator (no buffering all tracks in memory at once). Rate limiting (HTTP 429) is handled with `Retry-After` sleep and up to 3 retries.

## Acceptance Criteria

- [x] `resolve_artist(sp, name)` returns `{id, name}` for a valid artist name
- [x] Artist not found — `ArtistNotFoundError` is raised (not a crash or silent failure)
- [x] `fetch_albums(sp, artist_id, ...)` paginates through all pages when `page_all=True` (not just first 50)
- [x] `--from-year` / `--to-year` filters applied correctly by `apply_year_filter()`; albums outside range excluded
- [x] `--album-type single` returns only singles; album tracks are absent from output
- [x] `iter_tracks()` is a generator — it does not load all tracks into memory before yielding the first
- [x] HTTP 429 triggers sleep using `Retry-After` header value, retried up to 3 times before raising

## Technical Notes

### Implementation Approach

All functions are pure and accept a `spotipy.Spotify` instance as first argument — no module-level state. This makes the module trivially testable with `MagicMock`. The `iter_tracks()` generator yields one track dict per iteration, enabling the command layer to stream NDJSON without buffering.

### Code Examples

```python
# spotify_cli/discography/fetcher.py
from __future__ import annotations

import time
from typing import Generator
import spotipy


class ArtistNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No Spotify artist matched '{name}'")


def resolve_artist(sp: spotipy.Spotify, name: str) -> dict:
    results = sp.search(q=name, type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])
    if not items:
        raise ArtistNotFoundError(name)
    artist = items[0]
    return {"id": artist["id"], "name": artist["name"]}


def fetch_albums(
    sp: spotipy.Spotify,
    artist_id: str,
    album_type: str = "album",
    page_all: bool = False,
) -> list[dict]:
    api_album_type = (
        "album,single,compilation,appears_on" if album_type == "all" else album_type
    )
    albums: list[dict] = []
    response = sp.artist_albums(artist_id, album_type=api_album_type, limit=50)
    while response:
        albums.extend(response["items"])
        response = sp.next(response) if (page_all and response.get("next")) else None
    return albums


def apply_year_filter(
    albums: list[dict],
    from_year: int | None = None,
    to_year: int | None = None,
) -> list[dict]:
    def year_of(album: dict) -> int:
        # release_date can be "YYYY", "YYYY-MM", or "YYYY-MM-DD"
        return int(album["release_date"][:4])

    return [
        a for a in albums
        if (from_year is None or year_of(a) >= from_year)
        and (to_year is None or year_of(a) <= to_year)
    ]


def iter_tracks(
    sp: spotipy.Spotify,
    albums: list[dict],
    artist_name: str,
) -> Generator[dict, None, None]:
    for album in albums:
        response = sp.album_tracks(album["id"], limit=50)
        while response:
            for track in response["items"]:
                yield {
                    "uri": track["uri"],
                    "name": track["name"],
                    "artist": artist_name,
                    "album": album["name"],
                    "release_date": album["release_date"],
                    "track_number": track["track_number"],
                    "duration_ms": track["duration_ms"],
                    "explicit": track["explicit"],
                }
            response = sp.next(response) if response.get("next") else None
```

### Representative Tests

```python
# tests/discography/test_fetcher.py — artist not found
def test_resolve_artist_raises_when_not_found():
    sp = MagicMock()
    sp.search.return_value = {"artists": {"items": []}}
    with pytest.raises(ArtistNotFoundError, match="No Spotify artist matched"):
        resolve_artist(sp, "Nonexistent Artist XYZ")

# iter_tracks is a generator (not a list)
def test_iter_tracks_is_generator():
    from inspect import isgeneratorfunction
    assert isgeneratorfunction(iter_tracks)
```

### Files/Components Affected

- `spotify_cli/discography/fetcher.py` — new file (create)
- `tests/discography/test_fetcher.py` — new file (create)

### External Dependencies

- `spotipy ≥ 2.25.1` — `sp.search()`, `sp.artist_albums()`, `sp.album_tracks()`, `sp.next()` — already in `pyproject.toml`

## Definition of Done

- [x] Code implemented and follows conventions
- [x] All acceptance criteria met
- [x] Tests written and passing (`uv run pytest tests/discography/test_fetcher.py -v`)
- [x] Spotipy fully mocked — no live API calls in tests
- [x] Self-reviewed
- [x] No known bugs or issues

## Dependencies

**Depends On**:
- E2-S1: Cache Module — no hard dependency at the fetcher level, but both are needed before E2-S3

**Blocks**:
- E2-S3: Discography Command — imports `resolve_artist`, `fetch_albums`, `apply_year_filter`, `iter_tracks`
- E2-S4: Discography Tests — `test_fetcher.py` tests this module

## Related Stories

- E2-S1: Cache Module — complements fetcher as the two data-layer modules
- E2-S3: Discography Command — orchestrates fetcher and cache together
- E2-S4: Discography Tests — fetcher tests are a deliverable of S4

## Notes

- Rate limit handling (429): wrap `sp.artist_albums()` and `sp.album_tracks()` calls in a retry loop; catch `spotipy.exceptions.SpotifyException` with HTTP status 429; read `Retry-After` header (default 1s if absent); `time.sleep()` then retry up to 3 times.
- `album_type == "all"` maps to `"album,single,compilation,appears_on"` — spotipy's `artist_albums()` accepts comma-separated type strings.
- `release_date` from Spotify can be `"YYYY"`, `"YYYY-MM"`, or `"YYYY-MM-DD"` — `apply_year_filter` must handle all three by slicing `[:4]`.

---

**Created**: 2026-06-04
**Status**: ✅ Done (Sprint-03, 2026-06-11)
