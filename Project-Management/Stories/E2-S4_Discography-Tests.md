# Story: Discography Tests

**Epic**: [E2 - Discography Browse](../Epics/E2_Discography-Browse.md)
**Story ID**: E2-S4
**Story Points**: 3
**Priority**: Medium
**Status**: To Do

## User Story

As a **developer**,
I want a **full test suite for the discography module**,
So that **cache logic, API traversal, and command output are all verified before the command is shipped**.

## Description

Write the complete test suite for the `spotify_cli/discography/` package: three test files covering `cache.py`, `fetcher.py`, and `commands.py`. All 12 test cases from SPEC-002 (TC-01 through TC-12) must be implemented. Spotipy is fully mocked — no live API calls. Cache tests use `monkeypatch` to redirect `CACHE_DIR` to a temp directory. Command tests use Typer's `CliRunner`.

## Acceptance Criteria

- [ ] All TC-01 through TC-11 from SPEC-002 pass via `uv run pytest tests/discography/ -v`
- [ ] Cache TTL expiry is tested with mocked `datetime.now()` (no real-time waiting)
- [ ] Spotipy is fully mocked — no live API calls in any test
- [ ] Coverage ≥ 80% for all discography modules (`commands.py`, `fetcher.py`, `cache.py`)
- [ ] Invalid `--album-type` value — exit 3 is tested (TC-10)
- [ ] Corrupt cache treated as miss — tested (TC-11)

## Technical Notes

### Implementation Approach

Three test files, one per module. Test isolation via `monkeypatch` for cache dir and `unittest.mock.patch` for spotipy and auth. Command tests use `typer.testing.CliRunner` to invoke the command in-process.

### Test Matrix

| TC | Scenario | Test File | Strategy |
|----|----------|-----------|----------|
| TC-01 | Valid artist, cache miss → fetch + stream + cache write, exits 0 | `test_commands.py` | Mock fetcher, mock cache.is_valid=False |
| TC-02 | Valid artist, cache hit (within TTL) → reads cache, zero API calls, exits 0 | `test_commands.py` | Mock cache.is_valid=True, mock cache.read |
| TC-03 | `--no-cache` → skips cache read, fetches fresh, overwrites cache, exits 0 | `test_commands.py` | Mock fetcher, assert cache.write called |
| TC-04 | Artist not found → stderr JSON `error: artist not found`, exits 4 | `test_commands.py` | raise ArtistNotFoundError in mock |
| TC-05 | `--from-year 1960 --to-year 1970` → only tracks from that decade | `test_commands.py` | Mock albums with mixed release years |
| TC-06 | `--album-type single` → only singles in output | `test_commands.py` | Mock fetch_albums to verify arg passed |
| TC-07 | Not authenticated → stderr JSON `error: not authenticated`, exits 1 | `test_commands.py` | raise NotAuthenticatedError in mock |
| TC-08 | Cache expired (>24h) → treated as miss, fetch fresh, exits 0 | `test_cache.py` | monkeypatch datetime.now |
| TC-09 | `--page-all` on artist with 60+ albums → streams all tracks | `test_fetcher.py` | Mock sp.next to return second page |
| TC-10 | `--album-type invalid-value` → stderr JSON `error: validation error`, exits 3 | `test_commands.py` | Invoke with bad --album-type value |
| TC-11 | Cache file corrupt (invalid JSON) → cache miss, fetches fresh | `test_cache.py` | Write corrupt JSON to cache file |
| TC-12 | stdout piped (not TTY) → valid NDJSON, no ANSI codes | `test_commands.py` | CliRunner captures stdout, validate JSON |

### Code Examples

```python
# tests/discography/test_cache.py — representative tests
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from unittest.mock import patch

from spotify_cli.discography import cache as cache_mod


def test_is_valid_returns_false_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    assert cache_mod.is_valid("nonexistent") is False


def test_write_then_read_returns_same_tracks(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    tracks = [{"uri": "spotify:track:001", "name": "Hurt"}]
    cache_mod.write("abc", "Johnny Cash", tracks)
    assert cache_mod.is_valid("abc") is True
    assert cache_mod.read("abc") == tracks


def test_is_valid_returns_false_when_ttl_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    expired_at = (datetime.now(timezone.utc) - timedelta(seconds=86401)).isoformat().replace("+00:00", "Z")
    payload = {"artist_id": "abc", "artist_name": "Test", "cached_at": expired_at, "ttl_seconds": 86400, "tracks": []}
    (tmp_path / "abc.json").write_text(json.dumps(payload))
    assert cache_mod.is_valid("abc") is False


def test_corrupt_cache_file_treated_as_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    (tmp_path / "abc.json").write_text("not valid json{{{")
    assert cache_mod.is_valid("abc") is False
    assert cache_mod.read("abc") == []


def test_write_uses_atomic_tmp_then_rename(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    cache_mod.write("abc", "Johnny Cash", [])
    assert (tmp_path / "abc.json").exists()
    assert not (tmp_path / "abc.tmp").exists()


def test_clear_removes_all_cache_files(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    cache_mod.write("abc", "Johnny Cash", [])
    cache_mod.write("def", "Bob Dylan", [])
    cache_mod.clear()
    assert list(tmp_path.glob("*.json")) == []
```

```python
# tests/discography/test_fetcher.py — representative tests
from unittest.mock import MagicMock
import pytest
from spotify_cli.discography.fetcher import (
    resolve_artist, ArtistNotFoundError, fetch_albums, apply_year_filter, iter_tracks
)


def test_resolve_artist_returns_id_and_name():
    sp = MagicMock()
    sp.search.return_value = {"artists": {"items": [{"id": "abc123", "name": "Johnny Cash"}]}}
    result = resolve_artist(sp, "Johnny Cash")
    assert result == {"id": "abc123", "name": "Johnny Cash"}


def test_resolve_artist_raises_when_not_found():
    sp = MagicMock()
    sp.search.return_value = {"artists": {"items": []}}
    with pytest.raises(ArtistNotFoundError, match="No Spotify artist matched"):
        resolve_artist(sp, "Nonexistent Artist XYZ")


def test_fetch_albums_paginates_when_page_all(mocker):
    sp = MagicMock()
    page1 = {"items": [{"id": "alb1"}], "next": "url"}
    page2 = {"items": [{"id": "alb2"}], "next": None}
    sp.artist_albums.return_value = page1
    sp.next.return_value = page2
    albums = fetch_albums(sp, "artist1", page_all=True)
    assert len(albums) == 2
    sp.next.assert_called_once()


def test_apply_year_filter_excludes_out_of_range():
    albums = [
        {"id": "a1", "release_date": "1959-01-01"},
        {"id": "a2", "release_date": "1965-06-15"},
        {"id": "a3", "release_date": "1971-03-20"},
    ]
    result = apply_year_filter(albums, from_year=1960, to_year=1970)
    assert len(result) == 1
    assert result[0]["id"] == "a2"
```

```python
# tests/discography/test_commands.py — TC-01 and TC-07 representative
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from spotify_cli.discography.commands import app
from spotify_cli.discography.fetcher import ArtistNotFoundError
from spotify_cli.auth.spotify_client import NotAuthenticatedError
import json

runner = CliRunner()


def test_browse_cache_miss_fetches_and_streams():
    mock_tracks = [
        {"uri": "spotify:track:001", "name": "Hurt", "artist": "Johnny Cash",
         "album": "American IV", "release_date": "2002-11-05",
         "track_number": 1, "duration_ms": 220000, "explicit": False}
    ]
    with patch("spotify_cli.discography.commands.cache.is_valid", return_value=False), \
         patch("spotify_cli.discography.commands.cache.write"), \
         patch("spotify_cli.discography.commands.get_spotify_client", return_value=MagicMock()), \
         patch("spotify_cli.discography.commands.resolve_artist", return_value={"id": "abc", "name": "Johnny Cash"}), \
         patch("spotify_cli.discography.commands.fetch_albums", return_value=[]), \
         patch("spotify_cli.discography.commands.apply_year_filter", return_value=[]), \
         patch("spotify_cli.discography.commands.iter_tracks", return_value=iter(mock_tracks)):
        result = runner.invoke(app, ["Johnny Cash"])
    assert result.exit_code == 0
    line = json.loads(result.output.strip().splitlines()[0])
    assert line["uri"] == "spotify:track:001"


def test_browse_not_authenticated_exits_1():
    with patch("spotify_cli.discography.commands.get_spotify_client", side_effect=NotAuthenticatedError()):
        result = runner.invoke(app, ["Johnny Cash"])
    assert result.exit_code == 1
    err = json.loads(result.output)
    assert err["error"] == "not authenticated"
```

### Files/Components Affected

- `tests/discography/__init__.py` — new file (empty, marks test package)
- `tests/discography/test_cache.py` — new file (Phase 1 tests)
- `tests/discography/test_fetcher.py` — new file (Phase 2 tests)
- `tests/discography/test_commands.py` — new file (TC-01 through TC-12)

### External Dependencies

- `pytest` — test runner (`uv run pytest`)
- `pytest-cov` — coverage reporting (`--cov=spotify_cli/discography`)
- `unittest.mock` — stdlib mocking for spotipy and cache
- `typer.testing.CliRunner` — in-process CLI invocation

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] All 12 test cases pass: `uv run pytest tests/discography/ -v`
- [ ] Coverage ≥ 80%: `uv run pytest tests/discography/ --cov=spotify_cli/discography --cov-report=term-missing`
- [ ] Self-reviewed
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E2-S1: Cache Module — tests import `spotify_cli.discography.cache`
- E2-S2: Fetcher Module — tests import `spotify_cli.discography.fetcher`
- E2-S3: Discography Command — tests invoke `spotify_cli.discography.commands.app`

**Blocks**:
- None — this is the final story in EP-002

## Related Stories

- E2-S1: Cache Module — `test_cache.py` is this story's primary deliverable for S1
- E2-S2: Fetcher Module — `test_fetcher.py` is this story's primary deliverable for S2
- E2-S3: Discography Command — `test_commands.py` is this story's primary deliverable for S3

## Notes

- `CliRunner` from Typer captures stdout and stderr in `result.output`. Note that by default `mix_stderr=True` — set `mix_stderr=False` on `CliRunner()` if you need to assert on stderr separately from stdout.
- Use `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)` — not `monkeypatch.setattr(cache_mod, "cache_path", ...)` — so that `CACHE_DIR` is redirected at the module level and all path operations derive from it consistently.
- TC-08 (cache TTL expiry) does not require `time.sleep` — monkeypatch `datetime.now` to return a time 25 hours in the past.
- TC-12 (no ANSI in piped output): `CliRunner` simulates a non-TTY environment by default, so `sys.stdout.isatty()` returns False during tests.

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
