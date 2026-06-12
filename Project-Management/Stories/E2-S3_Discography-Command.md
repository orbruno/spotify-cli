# Story: Discography Command

**Epic**: [E2 - Discography Browse](../Epics/E2_Discography-Browse.md)
**Story ID**: E2-S3
**Story Points**: 5
**Priority**: High
**Status**: To Do

## User Story

As an **AI agent**,
I want to run **`spotify-cli discography "Johnny Cash"` and receive a stream of all his tracks as NDJSON**,
So that **I can select tracks from verified Spotify URIs to build a playlist without any URI resolution step**.

## Description

Create `spotify_cli/discography/commands.py` — the Typer command group that serves as the entrypoint for the discography feature. The command orchestrates: auth check → cache check → fetch (on miss) → cache write → NDJSON stream to stdout. All errors go to stderr as structured JSON with semantic exit codes. Register the command group in `spotify_cli/main.py`.

## Acceptance Criteria

- [ ] `discography "Johnny Cash"` streams NDJSON to stdout, exits 0
- [ ] Each line of stdout is a valid, parseable JSON object matching the output schema
- [ ] Cache hit — no API calls made, same output as fresh fetch
- [ ] `--no-cache` — bypasses cache read, fetches fresh from API, overwrites cache
- [ ] Artist not found — structured JSON on stderr (`error: artist not found`), exits 4, stdout empty
- [ ] Not authenticated — structured JSON on stderr (`error: not authenticated`), exits 1, stdout empty
- [ ] ANSI codes absent from stdout when piped (non-TTY context)
- [ ] `--from-year 1960 --to-year 1970` returns only tracks from albums in that decade
- [ ] `--album-type invalid-value` — structured JSON on stderr (`error: validation error`), exits 3
- [ ] Command accessible as `spotify-cli discography` after registration in `main.py`

## Technical Notes

### Implementation Approach

Command delegates to `cache.py` and `fetcher.py` — it contains no business logic itself. Track collection happens in two phases: (1) collect all tracks into a list (needed to write cache after full traversal), (2) stream from that list. This ensures the cache is never written partially.

### Code Examples

```python
# spotify_cli/discography/commands.py
from __future__ import annotations

import json
import sys
from enum import Enum
from typing import Optional

import typer

from spotify_cli.core.spotify_client import get_spotify_client, NotAuthenticatedError
from spotify_cli.discography import cache
from spotify_cli.discography.fetcher import (
    ArtistNotFoundError,
    apply_year_filter,
    fetch_albums,
    iter_tracks,
    resolve_artist,
)

app = typer.Typer(name="discography", help="Browse an artist's full track catalogue.")


class AlbumType(str, Enum):
    album = "album"
    single = "single"
    compilation = "compilation"
    all = "all"


def emit(track: dict) -> None:
    line = json.dumps(track, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _error_exit(error: str, reason: str, suggestion: str, help_cmd: str, code: int) -> None:
    payload = {
        "error": error,
        "reason": reason,
        "suggestion": suggestion,
        "help": help_cmd,
    }
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stderr.flush()
    raise typer.Exit(code=code)


@app.command()
def browse(
    artist_name: str = typer.Argument(..., help="Artist name to look up"),
    album_type: AlbumType = typer.Option(AlbumType.album, "--album-type", help="Album type filter"),
    from_year: Optional[int] = typer.Option(None, "--from-year", help="Earliest release year (inclusive)"),
    to_year: Optional[int] = typer.Option(None, "--to-year", help="Latest release year (inclusive)"),
    page_all: bool = typer.Option(False, "--page-all", help="Fetch all album pages (default: first page only)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache, force fresh API fetch"),
    fmt: str = typer.Option("json", "--format", help="Output format (currently: json)"),
) -> None:
    # Auth check
    try:
        sp = get_spotify_client()
    except NotAuthenticatedError:
        _error_exit(
            error="not authenticated",
            reason="No valid token in cache",
            suggestion="Run spotify-cli auth login first",
            help_cmd="spotify-cli auth login",
            code=1,
        )

    # Resolve artist to get ID for cache key
    try:
        artist = resolve_artist(sp, artist_name)
    except ArtistNotFoundError as exc:
        _error_exit(
            error="artist not found",
            reason=f"No Spotify artist matched '{exc.name}'",
            suggestion="Check spelling or try a more specific name",
            help_cmd="spotify-cli discography --help",
            code=4,
        )

    # Cache check
    if not no_cache and cache.is_valid(artist["id"]):
        tracks = cache.read(artist["id"])
    else:
        albums = fetch_albums(sp, artist["id"], album_type=album_type.value, page_all=page_all)
        albums = apply_year_filter(albums, from_year=from_year, to_year=to_year)
        tracks = list(iter_tracks(sp, albums, artist["name"]))
        cache.write(artist["id"], artist["name"], tracks)

    for track in tracks:
        emit(track)
```

```python
# spotify_cli/main.py — add alongside existing auth registration
from spotify_cli.discography.commands import app as discography_app

app.add_typer(discography_app)
```

### Output Schema (per line)

```json
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
```

### Error Schema (stderr)

| Scenario | Exit Code | `error` | `suggestion` |
|----------|-----------|---------|--------------|
| Artist not found | 4 | `"artist not found"` | `"Check spelling or try a more specific name"` |
| Not authenticated | 1 | `"not authenticated"` | `"Run spotify-cli auth login first"` |
| Validation error (bad flag) | 3 | `"validation error"` | `"Valid values: album, single, compilation, all"` |
| API rate limit (post-retry) | 4 | `"rate limited"` | `"Wait and retry"` |

### Files/Components Affected

- `spotify_cli/discography/commands.py` — new file (create)
- `spotify_cli/main.py` — modified (register discography app)
- `tests/discography/test_commands.py` — new file (create, covered in E2-S4)

### External Dependencies

- `typer` — CLI framework (already in `pyproject.toml`)
- `spotify_cli.core.spotify_client` — `get_spotify_client()`, `NotAuthenticatedError` (delivered in Sprint-03 Wave 0; canonical location — SPEC-002's reference to an auth-package client module is a stale spec error)
- `spotify_cli.discography.cache` — E2-S1
- `spotify_cli.discography.fetcher` — E2-S2

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] `spotify-cli discography "Johnny Cash"` streams NDJSON to terminal, exits 0 (manual verify)
- [ ] `discography` command accessible from root CLI (`spotify-cli --help` lists it)
- [ ] Self-reviewed
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E2-S1: Cache Module — `cache.is_valid()`, `cache.read()`, `cache.write()` required
- E2-S2: Fetcher Module — `resolve_artist()`, `fetch_albums()`, `apply_year_filter()`, `iter_tracks()` required
- EP-001 (E1): `spotify_client.py` must be implemented before this story can run end-to-end

**Blocks**:
- E2-S4: Discography Tests — `test_commands.py` tests this command

## Related Stories

- E2-S1: Cache Module — provides cache read/write
- E2-S2: Fetcher Module — provides API traversal
- E2-S4: Discography Tests — verifies TC-01 through TC-12 against this command

## Notes

- `emit()` uses `sys.stdout.write()` + `sys.stdout.flush()` for immediate line-by-line output. Do not use `print()` — it buffers by default in some environments.
- ANSI stripping: when `not sys.stdout.isatty()`, ensure no ANSI codes are present. Since `emit()` only writes plain JSON, this is satisfied without explicit stripping — but verify in test with piped output.
- `--format` flag is reserved for future `csv`/`table` modes. For now, validate that only `"json"` is accepted; any other value exits 3.
- Cache is written after all tracks are collected (not incrementally) to guarantee the cache file is always complete.

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
