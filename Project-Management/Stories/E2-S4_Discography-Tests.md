# Story: Discography Tests

**Epic**: [E2 - Discography Browse](../Epics/E2_Discography-Browse.md)
**Story ID**: E2-S4
**Story Points**: 3
**Priority**: Medium
**Status**: To Do

## User Story

As a **developer**,
I want a **command-level test suite and coverage gate for the discography package**,
So that **command behavior, the cache + fetcher + command integration, and the package coverage threshold are all verified before the command is shipped**.

## Description

Complete the test suite for the `spotify_cli/discography/` package. The unit suites for `cache.py` and `fetcher.py` were **delivered in Sprint-03** (`tests/discography/test_cache.py`, 8 tests; `tests/discography/test_fetcher.py`, 15 tests) — do not recreate them. This story adds `tests/discography/test_commands.py` covering the command-level test cases from SPEC-002, verifies the cache → fetch → cache-write → NDJSON-stream integration, and enforces the ≥80% coverage gate for the whole discography package. Spotipy is fully mocked — no live API calls. Command tests use Typer's `CliRunner`.

## Acceptance Criteria

- [ ] All TC-01 through TC-11 from SPEC-002 pass via `uv run pytest tests/discography/ -v` (TC-08, TC-09, TC-11 already pass via the Sprint-03 cache/fetcher suites)
- [ ] Command test cases (TC-01–TC-07, TC-10, TC-12) implemented in `tests/discography/test_commands.py`
- [ ] Spotipy is fully mocked — no live API calls in any test
- [ ] Coverage ≥ 80% for all discography modules (`commands.py`, `fetcher.py`, `cache.py`)
- [ ] Invalid `--album-type` value — exit 3 is tested (TC-10)
- [ ] Cache + fetcher + command integration verified: cache-miss path calls fetcher and writes cache; cache-hit path makes zero API calls

## Technical Notes

### Implementation Approach

One new test file: `tests/discography/test_commands.py` (the cache and fetcher suites already exist from Sprint-03 — extend them only if a TC gap is found). Test isolation via `unittest.mock.patch` for spotipy and auth (stdlib only — pytest-mock is not a dependency). Command tests use `typer.testing.CliRunner` to invoke the command in-process. Finish with the package-wide coverage gate.

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
| TC-08 | Cache expired (>24h) → treated as miss, fetch fresh, exits 0 | `test_cache.py` | ✅ Done (Sprint-03) — past `cached_at` timestamp, no datetime patching |
| TC-09 | `--page-all` on artist with 60+ albums → streams all tracks | `test_fetcher.py` | ✅ Done (Sprint-03) — `sp.next` returns second page |
| TC-10 | `--album-type invalid-value` → stderr JSON `error: validation error`, exits 3 | `test_commands.py` | Invoke with bad --album-type value |
| TC-11 | Cache file corrupt (invalid JSON) → cache miss, fetches fresh | `test_cache.py` | ✅ Done (Sprint-03) — corrupt JSON written to cache file |
| TC-12 | stdout piped (not TTY) → valid NDJSON, no ANSI codes | `test_commands.py` | CliRunner captures stdout, validate JSON |

### Existing Suites (delivered in Sprint-03 — do not recreate)

- `tests/discography/test_cache.py` — 8 tests: miss, write→read roundtrip, TTL expiry (past `cached_at` timestamp), corrupt JSON as miss, missing `cached_at` key, atomic write, `clear()`, missing-file read. All isolated via `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)`.
- `tests/discography/test_fetcher.py` — 15 tests: artist resolution, pagination (`page_all` on/off), album-type mapping, year filter (all three date formats), generator semantics, full 429 retry contract. All mocking via stdlib `unittest.mock` (`MagicMock`, `patch`).

Extend these files only if a SPEC-002 TC gap is discovered; this story's new work is `test_commands.py`.

### Code Examples

```python
# tests/discography/test_commands.py — TC-01 and TC-07 representative
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from spotify_cli.discography.commands import app
from spotify_cli.discography.fetcher import ArtistNotFoundError
from spotify_cli.core.spotify_client import NotAuthenticatedError
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

- `tests/discography/__init__.py` — ✅ exists (Sprint-03)
- `tests/discography/test_cache.py` — ✅ exists (Sprint-03); extend only if a TC gap is found
- `tests/discography/test_fetcher.py` — ✅ exists (Sprint-03); extend only if a TC gap is found
- `tests/discography/test_commands.py` — new file (command TCs: TC-01–TC-07, TC-10, TC-12)

### External Dependencies

- `pytest` — test runner (`uv run pytest`)
- `pytest-cov` — coverage reporting (`--cov=spotify_cli/discography`)
- `unittest.mock` — stdlib mocking for spotipy, auth, and cache (pytest-mock is NOT a dependency and must not be added)
- `typer.testing.CliRunner` — in-process CLI invocation
- `spotify_cli.core.spotify_client` — `get_spotify_client()`, `NotAuthenticatedError` (canonical location, delivered in Sprint-03 Wave 0)

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] All 12 test cases pass: `uv run pytest tests/discography/ -v`
- [ ] Coverage ≥ 80%: `uv run pytest tests/discography/ --cov=spotify_cli/discography --cov-report=term-missing`
- [ ] Self-reviewed
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E2-S1: Cache Module — ✅ Done (Sprint-03), including `test_cache.py`
- E2-S2: Fetcher Module — ✅ Done (Sprint-03), including `test_fetcher.py`
- E2-S3: Discography Command — tests invoke `spotify_cli.discography.commands.app`

**Blocks**:
- None — this is the final story in EP-002

## Related Stories

- E2-S1: Cache Module — `test_cache.py` delivered with S1 in Sprint-03
- E2-S2: Fetcher Module — `test_fetcher.py` delivered with S2 in Sprint-03
- E2-S3: Discography Command — `test_commands.py` is this story's primary deliverable

## Notes

- `CliRunner` from Typer captures stdout and stderr in `result.output`. Note that by default `mix_stderr=True` — set `mix_stderr=False` on `CliRunner()` if you need to assert on stderr separately from stdout.
- Use `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)` — not `monkeypatch.setattr(cache_mod, "cache_path", ...)` — so that `CACHE_DIR` is redirected at the module level and all path operations derive from it consistently.
- TC-08 (cache TTL expiry) is already covered in Sprint-03's `test_cache.py` — by writing a `cached_at` timestamp 86401s in the past; no `time.sleep` and no datetime patching needed.
- TC-12 (no ANSI in piped output): `CliRunner` simulates a non-TTY environment by default, so `sys.stdout.isatty()` returns False during tests.

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
