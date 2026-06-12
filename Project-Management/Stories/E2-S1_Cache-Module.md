# Story: Cache Module

**Epic**: [E2 - Discography Browse](../Epics/E2_Discography-Browse.md)
**Story ID**: E2-S1
**Story Points**: 3
**Priority**: High
**Status**: ✅ Done

## User Story

As a **developer**,
I want a **file-based cache module for discography data with 24h TTL**,
So that **repeated calls for the same artist don't hit the Spotify API unnecessarily**.

## Description

Create `spotify_cli/discography/cache.py` — a pure stdlib module that stores and retrieves per-artist discography results from `~/.config/spotify-cli/cache/discography/{artist_id}.json`. The module must check TTL validity, write atomically to prevent corrupt reads, and handle corrupt cache files gracefully (treat as miss, not crash). No third-party cache libraries — stdlib `json`, `pathlib`, and `datetime` only.

## Acceptance Criteria

- [x] Cache miss — `is_valid()` returns False when file does not exist
- [x] After `write()` — `is_valid()` returns True and `read()` returns the same tracks list
- [x] TTL expired (>24h since `cached_at`) — `is_valid()` returns False
- [x] Atomic write — data is written to a `.tmp` file then renamed to the final path; no partial file visible to readers
- [x] Corrupt JSON cache file — `is_valid()` returns False (treated as miss, not exception); `read()` returns empty list
- [x] `clear()` removes all files in `~/.config/spotify-cli/cache/discography/`
- [x] Unit tests cover all above scenarios

## Technical Notes

### Implementation Approach

Single-file module. All functions are pure and stateless. `CACHE_DIR` and `TTL_SECONDS` are module-level constants.

### Code Examples

```python
# spotify_cli/discography/cache.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path.home() / ".config" / "spotify-cli" / "cache" / "discography"
TTL_SECONDS = 86400  # 24 hours


def cache_path(artist_id: str) -> Path:
    return CACHE_DIR / f"{artist_id}.json"


def is_valid(artist_id: str) -> bool:
    path = cache_path(artist_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data["cached_at"].replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
        return age_seconds < TTL_SECONDS
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def read(artist_id: str) -> list[dict]:
    path = cache_path(artist_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("tracks", [])
    except (json.JSONDecodeError, OSError):
        return []


def write(artist_id: str, artist_name: str, tracks: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "artist_id": artist_id,
        "artist_name": artist_name,
        "cached_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ttl_seconds": TTL_SECONDS,
        "tracks": tracks,
    }
    target = cache_path(artist_id)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)  # atomic on POSIX


def clear() -> None:
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            f.unlink(missing_ok=True)
```

### Cache File Schema

```json
{
  "artist_id": "6kACVPfCOnqzgfEF5G9b9X",
  "artist_name": "Johnny Cash",
  "cached_at": "2026-06-04T14:00:00Z",
  "ttl_seconds": 86400,
  "tracks": [
    {
      "uri": "spotify:track:abc",
      "name": "Hurt",
      "artist": "Johnny Cash",
      "album": "American IV",
      "release_date": "2002-11-05",
      "track_number": 1,
      "duration_ms": 220000,
      "explicit": false
    }
  ]
}
```

### Representative Test (TTL expiry)

```python
# tests/discography/test_cache.py
def test_is_valid_returns_false_when_ttl_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    expired_at = (datetime.now(timezone.utc) - timedelta(seconds=86401)).isoformat().replace("+00:00", "Z")
    payload = {"artist_id": "abc", "artist_name": "Test", "cached_at": expired_at, "ttl_seconds": 86400, "tracks": []}
    (tmp_path / "abc.json").write_text(json.dumps(payload))
    assert cache_mod.is_valid("abc") is False
```

### Files/Components Affected

- `spotify_cli/discography/cache.py` — new file (create)
- `spotify_cli/discography/__init__.py` — new file (create, exports `cache`)
- `tests/discography/__init__.py` — new file (create, empty)
- `tests/discography/test_cache.py` — new file (create)

### External Dependencies

- stdlib only: `json`, `pathlib`, `datetime` — no third-party cache libs (NFR-07)

## Definition of Done

- [x] Code implemented and follows conventions
- [x] All acceptance criteria met
- [x] Tests written and passing (`uv run pytest tests/discography/test_cache.py -v`)
- [x] Self-reviewed
- [x] No known bugs or issues

## Dependencies

**Depends On**:
- None — this story has no story-level dependencies

**Blocks**:
- E2-S2: Fetcher Module uses `cache.write()` indirectly via the command
- E2-S3: Discography Command calls `cache.is_valid()`, `cache.read()`, `cache.write()`

## Related Stories

- E2-S2: Fetcher Module — data source for what gets cached
- E2-S3: Discography Command — orchestrates cache check vs. fetch
- E2-S4: Discography Tests — tests for this module live in `tests/discography/test_cache.py`

## Notes

- Use `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)` in tests to avoid writing to the real home directory.
- The `.tmp` → `rename()` pattern is atomic on POSIX (macOS/Linux). On Windows, `replace()` is also atomic, so this pattern is cross-platform safe.
- `clear()` uses `missing_ok=True` on `unlink()` to be idempotent — safe to call even if cache dir is empty or files were already deleted.

---

**Created**: 2026-06-04
**Status**: ✅ Done (Sprint-03, 2026-06-11)
