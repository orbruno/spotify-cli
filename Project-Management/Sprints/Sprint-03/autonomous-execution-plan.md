# Sprint-03 Autonomous Execution Plan

**Sprint Goal**: The codebase can resolve an artist name, paginate their full album catalogue, stream flat track dicts as a generator, and cache results to disk with a 24h TTL.
**Mode**: Fully autonomous — `--dangerously-skip-permissions`, no human intervention.
**Total**: 2 stories, 8 pts. Builds on top of Sprint-02 codebase in `spotify_cli/`.

Path convention (standard single-root layout):
- Sprint artifacts: `Project-Management/...` from the repo root.
- Code, tests, and all commands run from the repo root (`spotify-cli/`).
- Design docs: `_Design/...` from the repo root.

---

## How to Use This Plan

```bash
# Recommended: isolated worktree (keeps main checkout clean)
claude --worktree --dangerously-skip-permissions \
  "Read Project-Management/Sprints/Sprint-03/autonomous-execution-plan.md and execute it wave by wave."

# Alternative: run directly in working tree
claude --dangerously-skip-permissions \
  "Read Project-Management/Sprints/Sprint-03/autonomous-execution-plan.md and execute it wave by wave."
```

---

## Architecture Source of Truth

Read these files in priority order before writing any code:

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `Project-Management/Stories/E2-S1_Cache-Module.md` | E2-S1 acceptance criteria + exact cache implementation |
| 2 | `Project-Management/Stories/E2-S2_Fetcher-Module.md` | E2-S2 acceptance criteria + fetcher implementation (429 contract per Notes, NOT the spec) |
| 3 | `_Design/04_Specs/SPEC-002__discography-browse.md` | Feature spec — interfaces & track schema (subject to Conflict Resolution corrections below) |
| 4 | `spotify_cli/core/spotify_client.py` | Current auth baseline — Wave 0 EXTENDS this file; do not break `get_auth_manager` / `get_cached_token` / `require_client_id` |
| 5 | `tests/auth/test_auth_commands.py` | Test style reference — `unittest.mock`, `CliRunner`, monkeypatch patterns |
| 6 | `spotify_cli/main.py` | Typer registration pattern — DO NOT modify this sprint (no new commands until E2-S3) |
| 7 | `pyproject.toml` | Dependencies — no changes permitted this sprint |
| 8 | `_Design/03_ADR/ADR-002__sys__track-resolution-strategy.md` | Track-field rationale (where its cache schema drifts from SPEC-002 §1.7, SPEC-002 wins) |

---

## Conflict Resolution Rules

| Conflict | Resolution | Reference |
|----------|-----------|-----------|
| SPEC-002/E2-S3 import `spotify_cli.auth.spotify_client.get_spotify_client` + `NotAuthenticatedError` — **neither module nor symbols exist** | Wave 0 adds both to `spotify_cli/core/spotify_client.py` (canonical location). Never create `spotify_cli/auth/spotify_client.py`. | `spotify_cli/core/spotify_client.py` |
| E2-S2 example test uses `mocker` fixture (pytest-mock) — **not installed** | USE stdlib `unittest.mock` (`MagicMock`, `patch`) — do NOT add pytest-mock to pyproject | `pyproject.toml` dev group |
| SPEC-002 §3.1 says "single retry sufficient for MVP" vs story "retry up to 3 times" | USE 3 retries (1 initial call + up to 3 retries = max 4 calls), `Retry-After` default 1s | E2-S2 Notes; Sprint-03 stub |
| SPEC-002 §2.1 says `__init__.py` "exports DiscographyFetcher"; E2-S1 says it "exports cache" | USE empty `__init__.py` — no such class exists; submodule imports work without re-exports | E2-S3 imports `from spotify_cli.discography import cache` |
| SPEC-002 §2.4 names `invalidate(artist_id)`; story E2-S1 names `clear()` | USE `clear()` only (story is newer & internally consistent); do not implement `invalidate` | E2-S1 AC |
| SPEC-002 §1.3 claims token cache at `~/.config/spotify-cli/cache/token.json` | Real path is `~/.config/spotify-cli/.cache` (`CACHE_PATH` constant). Docs-only drift — no code impact this sprint | `spotify_cli/core/spotify_client.py:7` |
| ADR-002 cache schema uses `fetched_at` + per-track `album_type` | USE SPEC-002 §1.7 / E2-S1 schema: `cached_at` + the exact 8-field track dict | E2-S1 Cache File Schema |

---

## Pre-flight Assertions

Run from the repo root before dispatching any subagent. If any fail, STOP and report.

```bash
set -e

# Tooling
command -v uv >/dev/null || { echo "FAIL: uv not on PATH"; exit 1; }

# Sprint-02 baseline files exist
test -f spotify_cli/core/spotify_client.py || { echo "FAIL: core/spotify_client.py missing"; exit 1; }
test -f spotify_cli/main.py || { echo "FAIL: main.py missing"; exit 1; }
test -f tests/auth/test_auth_commands.py || { echo "FAIL: auth tests missing"; exit 1; }

# Sprint-03 source artifacts exist
test -f Project-Management/Stories/E2-S1_Cache-Module.md || { echo "FAIL: E2-S1 story missing"; exit 1; }
test -f Project-Management/Stories/E2-S2_Fetcher-Module.md || { echo "FAIL: E2-S2 story missing"; exit 1; }
test -f _Design/04_Specs/SPEC-002__discography-browse.md || { echo "FAIL: SPEC-002 missing"; exit 1; }

# Baseline test suite green (14 tests at planning time)
uv run pytest tests/ -x -q --tb=short

# Wave 0 target state check (informational)
test ! -d spotify_cli/discography \
  && echo "OK: discography package not yet present" \
  || echo "WARN: spotify_cli/discography already exists — check whether Wave 0 is partially done"

echo "PRE-FLIGHT PASSED"
```

Notes:
- No env vars required — every spotipy call in tests is mocked; `SPOTIFY_CLIENT_ID` is set via `monkeypatch` where needed.
- `pyproject.toml` has **no** `[tool.pytest.ini_options]` addopts — plain pytest commands are accurate; no `--no-cov` / `-o addopts=''` overrides needed.

---

## Story → Wave Mapping

```
Wave 0  │  Foundation: package __init__ files + auth client contract
         │  (get_spotify_client / NotAuthenticatedError in core/spotify_client.py)
         │
Wave 1  │  E2-S1 ─── Cache Module        (cache.py + test_cache.py)
(seq)    │  E2-S2 ─── Fetcher Module      (fetcher.py + test_fetcher.py)
         │
Wave 2  │  Integration verification (no code changes — run & report)
```

E2-S1 and E2-S2 share no files; they run sequentially to keep the working tree conflict-free.

---

## Wave 0 — Foundation (single agent, no skill invocation)

```
You are implementing Sprint-03 Wave 0 foundation work for the spotify-cli project.

READ FIRST:
- spotify_cli/core/spotify_client.py   (current implementation — you EXTEND it, do not rewrite)
- tests/auth/test_auth_commands.py     (test style reference)

CONFLICT RESOLUTION:
The auth client factory lives in spotify_cli/core/spotify_client.py. Do NOT create
spotify_cli/auth/spotify_client.py even though SPEC-002 references it — that path is
a spec error. NotAuthenticatedError is raised ONLY when get_cached_token() returns
None; token refresh is delegated to the SpotifyPKCE auth manager.

IMPLEMENT:

1. Create spotify_cli/discography/__init__.py — EMPTY file (no exports, no docstring required).
2. Create tests/discography/__init__.py — EMPTY file.
3. Create tests/core/__init__.py — EMPTY file.
4. APPEND to spotify_cli/core/spotify_client.py (keep all existing code unchanged):

class NotAuthenticatedError(Exception):
    """Raised when no cached Spotify token is available."""


def get_spotify_client() -> spotipy.Spotify:
    """
    Return an authenticated spotipy.Spotify instance.

    Raises NotAuthenticatedError if no cached token exists. Token refresh is
    delegated to the SpotifyPKCE auth manager. Command-layer callers must run
    require_client_id() first — this factory assumes SPOTIFY_CLIENT_ID is set.
    """
    if get_cached_token() is None:
        raise NotAuthenticatedError(
            "Not authenticated. Run 'spotify-cli auth login' first."
        )
    return spotipy.Spotify(auth_manager=get_auth_manager())

WRITE TESTS FIRST:
tests/core/test_spotify_client.py

import pytest
from unittest.mock import MagicMock, patch

from spotify_cli.core import spotify_client as client_mod
from spotify_cli.core.spotify_client import NotAuthenticatedError, get_spotify_client


def test_get_spotify_client_raises_when_no_cached_token():
    with patch.object(client_mod, "get_cached_token", return_value=None):
        with pytest.raises(NotAuthenticatedError, match="auth login"):
            get_spotify_client()


def test_get_spotify_client_returns_spotify_instance(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-client-id")
    token = {"access_token": "tok", "expires_at": 9999999999}
    mock_manager = MagicMock()
    with patch.object(client_mod, "get_cached_token", return_value=token), \
         patch.object(client_mod, "get_auth_manager", return_value=mock_manager), \
         patch.object(client_mod.spotipy, "Spotify") as mock_spotify:
        client = get_spotify_client()
    mock_spotify.assert_called_once_with(auth_manager=mock_manager)
    assert client is mock_spotify.return_value

VERIFY: uv run pytest tests/ -x -q must exit 0 (existing 14 tests + 2 new ones).
```

---

## Wave 1a — E2-S1: Cache Module

Invoke skill `everything-claude-code:tdd` first, then follow this prompt.

```
You are implementing E2-S1: Cache Module.

READ FIRST:
- Project-Management/Stories/E2-S1_Cache-Module.md   (acceptance criteria, DoD, exact code)
- spotify_cli/discography/__init__.py                (must already exist from Wave 0 — leave empty)

CONFLICT RESOLUTION:
- Implement clear() exactly as the story specifies. Do NOT implement invalidate()
  (SPEC-002 §2.4 drift). Do NOT add exports to discography/__init__.py.
- stdlib only: json, pathlib, datetime. No third-party imports (NFR-07).

IMPLEMENT spotify_cli/discography/cache.py with EXACTLY this content:

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
    tmp.replace(target)  # atomic on POSIX and Windows


def clear() -> None:
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            f.unlink(missing_ok=True)

WRITE TESTS FIRST:
tests/discography/test_cache.py

Every test MUST redirect the cache dir with
monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path) — never patch cache_path()
itself, and never touch the real home directory. Do NOT monkeypatch datetime or
use time.sleep — TTL expiry is tested by writing a past cached_at timestamp.

import json
from datetime import datetime, timedelta, timezone

from spotify_cli.discography import cache as cache_mod

TRACKS = [
    {
        "uri": "spotify:track:abc",
        "name": "Hurt",
        "artist": "Johnny Cash",
        "album": "American IV",
        "release_date": "2002-11-05",
        "track_number": 1,
        "duration_ms": 220000,
        "explicit": False,
    }
]

Test cases (one function each):
- test_is_valid_returns_false_when_file_missing: is_valid("missing") is False
- test_write_then_read_roundtrip: write("abc", "Johnny Cash", TRACKS) then
  is_valid("abc") is True and read("abc") == TRACKS
- test_is_valid_returns_false_when_ttl_expired: write a JSON file at
  tmp_path/"abc.json" whose cached_at is
  (datetime.now(timezone.utc) - timedelta(seconds=86401)).isoformat().replace("+00:00", "Z");
  is_valid("abc") is False
- test_corrupt_json_treated_as_miss: write "{not valid json" to tmp_path/"abc.json";
  is_valid("abc") is False AND read("abc") == []
- test_missing_cached_at_key_treated_as_miss: write json.dumps({"tracks": []});
  is_valid("abc") is False (KeyError path)
- test_write_is_atomic_no_tmp_file_left: after write(), (tmp_path/"abc.json").exists()
  is True AND (tmp_path/"abc.tmp").exists() is False
- test_clear_removes_all_json_files: write two artists, clear(),
  list(tmp_path.glob("*.json")) == []
- test_read_returns_empty_list_when_file_missing: read("missing") == [] (OSError path)

VERIFY: uv run pytest tests/discography/test_cache.py -v must exit 0.
```

---

## Wave 1b — E2-S2: Fetcher Module

Invoke skill `everything-claude-code:tdd` first, then follow this prompt.

```
You are implementing E2-S2: Fetcher Module.

READ FIRST:
- Project-Management/Stories/E2-S2_Fetcher-Module.md   (acceptance criteria, DoD)
- spotify_cli/discography/cache.py                     (sibling module — do NOT import it here)

CONFLICT RESOLUTION:
- USE stdlib unittest.mock (MagicMock, patch) — NOT the `mocker` fixture shown in the
  story's example test; pytest-mock is not installed and must not be added.
- USE 3 retries on HTTP 429 (1 initial call + up to 3 retries = max 4 calls),
  Retry-After header with default 1s — NOT SPEC-002 §3.1's "single retry" note.
- iter_tracks MUST remain a generator (contains yield). Do NOT "optimize" it into
  returning a list — NDJSON streaming in E2-S3 depends on lazy iteration.
- page_all=False returning only the first 50 albums is INTENDED behavior (SPEC FR-08).
  Do not "fix" it to always paginate.
- Wrap sp.artist_albums() and sp.album_tracks() with the retry helper; sp.next() is
  intentionally NOT wrapped (out of story scope).

IMPLEMENT spotify_cli/discography/fetcher.py with EXACTLY this content:

from __future__ import annotations

import time
from typing import Any, Callable, Generator

import spotipy
from spotipy.exceptions import SpotifyException

MAX_RETRIES = 3


class ArtistNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No Spotify artist matched '{name}'")


def _call_with_retry(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call a spotipy API method, retrying on HTTP 429 up to MAX_RETRIES times.

    Sleeps for the Retry-After header value (default 1s) between attempts.
    Non-429 errors and the final 429 are re-raised.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except SpotifyException as exc:
            if exc.http_status != 429 or attempt == MAX_RETRIES:
                raise
            headers = getattr(exc, "headers", None) or {}
            time.sleep(int(headers.get("Retry-After", 1)))


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
    response = _call_with_retry(
        sp.artist_albums, artist_id, album_type=api_album_type, limit=50
    )
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
        a
        for a in albums
        if (from_year is None or year_of(a) >= from_year)
        and (to_year is None or year_of(a) <= to_year)
    ]


def iter_tracks(
    sp: spotipy.Spotify,
    albums: list[dict],
    artist_name: str,
) -> Generator[dict, None, None]:
    for album in albums:
        response = _call_with_retry(sp.album_tracks, album["id"], limit=50)
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

WRITE TESTS FIRST:
tests/discography/test_fetcher.py

Mock spotipy with MagicMock(); set sp.search / sp.artist_albums / sp.album_tracks /
sp.next return values explicitly per test. Build 429 exceptions as:
SpotifyException(429, -1, "rate limited", headers={"Retry-After": "2"}).
Always patch time.sleep via patch("spotify_cli.discography.fetcher.time.sleep") so
tests never sleep for real.

Suggested helpers at module top:
def _album(name="Album", release_date="2002-11-05", album_id="alb1"):
    return {"id": album_id, "name": name, "release_date": release_date}
def _track(uri="spotify:track:abc", name="Hurt"):
    return {"uri": uri, "name": name, "track_number": 1, "duration_ms": 220000, "explicit": False}

Test cases (one function each):
- test_resolve_artist_returns_id_and_name: sp.search returns one artist
  {"id": "6kAC", "name": "Johnny Cash", "popularity": 80}; result == {"id": "6kAC",
  "name": "Johnny Cash"}; sp.search called with q="Johnny Cash", type="artist", limit=1
- test_resolve_artist_raises_when_not_found: empty items;
  pytest.raises(ArtistNotFoundError, match="No Spotify artist matched")
- test_fetch_albums_paginates_when_page_all: page1 has next="https://api/next",
  page2 has next=None via sp.next.return_value; fetch_albums(sp, "artist1",
  page_all=True) returns both albums; sp.next called exactly once with page1
- test_fetch_albums_default_returns_first_page_only: first page has next set;
  fetch_albums(sp, "artist1") returns 1 album; sp.next.assert_not_called()
- test_fetch_albums_maps_all_album_type: album_type="all" →
  sp.artist_albums kwargs album_type == "album,single,compilation,appears_on"
- test_fetch_albums_passes_single_album_type_through: album_type="single" →
  kwargs album_type == "single"
- test_apply_year_filter_excludes_out_of_range: albums dated "1994", "2002-11",
  "2010-05-01" with from_year=2000, to_year=2005 → only "2002-11" survives
  (proves YYYY / YYYY-MM / YYYY-MM-DD all handled)
- test_apply_year_filter_no_bounds_returns_all: no bounds → input returned unchanged
- test_iter_tracks_is_generator_function:
  from inspect import isgeneratorfunction; assert isgeneratorfunction(iter_tracks)
- test_iter_tracks_yields_flat_track_dicts: one album "American IV" dated
  "2002-11-05", one track; the yielded dict has EXACTLY the 8 fields
  uri, name, artist, album, release_date, track_number, duration_ms, explicit
  with artist == artist_name argument and album/release_date from the album dict
- test_iter_tracks_paginates_track_pages: track page1 next set, page2 via sp.next;
  both tracks yielded in order
- test_429_sleeps_and_retries_then_succeeds: func side_effect [429-exc, result];
  _call_with_retry returns result; time.sleep called once with 2; func called twice
- test_429_reraised_after_max_retries: func always raises 429;
  pytest.raises(SpotifyException); func.call_count == 4 (1 initial + 3 retries);
  sleep called 3 times
- test_429_defaults_to_one_second_without_header: headers={} → sleep called with 1
- test_non_429_spotify_exception_raises_immediately: SpotifyException(404, ...) →
  raised on first call; sleep never called

VERIFY: uv run pytest tests/discography/test_fetcher.py -v must exit 0.
```

---

## Wave 2 — Integration Verification (single agent, no skill invocation, NO code changes)

```
You are the Sprint-03 integration verification agent. You make NO code changes —
you run the checks below and produce a pass/fail report.

RUN (from the repo root), capturing exit codes:

1. uv run pytest tests/ -q                       # full suite: 14 baseline + Wave 0 + Wave 1
2. uv run pytest tests/discography/test_cache.py -v
3. uv run pytest tests/discography/test_fetcher.py -v
4. uv run python -c "from spotify_cli.core.spotify_client import get_spotify_client, NotAuthenticatedError"
5. uv run python -c "from spotify_cli.discography import cache, fetcher"
6. uv run python -c "from inspect import isgeneratorfunction; from spotify_cli.discography.fetcher import iter_tracks; assert isgeneratorfunction(iter_tracks)"
7. uv run spotify-cli --help
8. uv run spotify-cli auth status; echo "exit: $?"   # informational — depends on local token state
9. grep -rn "pytest_mock\|mocker" tests/discography/ && echo "FAIL: pytest-mock usage found" || echo "OK: no pytest-mock"
10. git diff --stat pyproject.toml | grep -q . && echo "FAIL: pyproject.toml modified" || echo "OK: pyproject untouched"
11. git status --porcelain spotify_cli/main.py | grep -q . && echo "FAIL: main.py modified" || echo "OK: main.py untouched"

REPORT: one line per check (PASS/FAIL + exit code), then an overall verdict.
Checks 1–7 and 9–11 must all pass for the sprint to be declarable done.
If any check fails, report the failure output verbatim — do NOT attempt fixes.
```

---

## Sprint Completion Checklist

After Wave 2 passes, the orchestrator updates all PM artifacts:

For each completed story (E2-S1, E2-S2):
- Update `Project-Management/Stories/E2-S1_Cache-Module.md` and `E2-S2_Fetcher-Module.md`: Status → "✅ Done"; check all Definition of Done checkboxes and acceptance criteria boxes.

Update `Project-Management/Sprints/Sprint-03/sprint-backlog.md`:
- Story Board: each story Status → "✅ Done"
- Points Tracker: Done column → 3 (E2-S1), 5 (E2-S2), total 8
- Append a Daily Progress row with the date and a one-line outcome

Update `Project-Management/Sprints/Sprint-03/README.md`:
- Status → "✅ Complete"; check all sprint-level DoD boxes that passed

Update `Project-Management/Backlog/Product-Backlog.md`:
- E2-S1 and E2-S2 rows: Status → ✅ Done
- EP-002 epic row: Complete → 50% (8/16 pts), Status → 🔄 In Progress
- Header "Sprint" line → "Sprint-03 (✅ complete) — next: Sprint-04 (E2-S3 + E2-S4)"
- Sprint Roadmap: Sprint-03 row Status → ✅ Complete

Update `Project-Management/README.md`:
- Current Focus → "Sprint-03 complete — discography data layer (cache + fetcher) done"
- Current Sprint quick link stays on Sprint-03 until Sprint-04 planning

Commit format (conventional commits, no AI attribution of any kind):
`feat: Sprint-03 — discography cache + fetcher modules (E2-S1, E2-S2)`

---

## Autonomous Decision Reference

| Decision | Answer | Source |
|----------|--------|--------|
| Where does `get_spotify_client()` live? | `spotify_cli/core/spotify_client.py` — never `auth/spotify_client.py` | Architecture consult; codebase |
| When is `NotAuthenticatedError` raised? | Only when `get_cached_token()` is `None`; refresh is the auth manager's job | Wave 0 spec above |
| Cache dir constant | `CACHE_DIR = Path.home() / ".config" / "spotify-cli" / "cache" / "discography"` | E2-S1 |
| TTL | `TTL_SECONDS = 86400`, compare `age_seconds < TTL_SECONDS` | E2-S1 |
| Atomic write | `tmp.write_text(...)` then `tmp.replace(target)`; test asserts no `.tmp` left | E2-S1 |
| Cache test isolation | `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)` — patch the constant, never `cache_path()` | E2-S1 Notes |
| TTL expiry test | Write past `cached_at` (now − 86401s); no `time.sleep`, no datetime patching | E2-S1 representative test |
| 429 retry count | 3 retries (max 4 calls), then re-raise | E2-S2 Notes (overrides SPEC-002 §3.1) |
| Retry-After access | `getattr(exc, "headers", None) or {}` then `int(headers.get("Retry-After", 1))` | spotipy `SpotifyException.headers` |
| Which calls get retry wrapping | `sp.artist_albums()`, `sp.album_tracks()` — not `sp.next()`, not `sp.search()` | E2-S2 Notes |
| `album_type="all"` mapping | `"album,single,compilation,appears_on"` | E2-S2 |
| `page_all=False` behavior | First page only (50 albums) — intended, do not "fix" | SPEC-002 FR-08 |
| Track dict fields | Exactly: `uri, name, artist, album, release_date, track_number, duration_ms, explicit` | SPEC-002 §1.7 / all stories |
| `iter_tracks` semantics | Generator (`yield`) — command layer materializes, fetcher never does | E2-S2 AC |
| Mock strategy | `unittest.mock` only; `MagicMock()` for `sp`; patch `fetcher.time.sleep` in retry tests | `tests/auth/test_auth_commands.py` convention |
| New dependencies | None — do not touch `pyproject.toml` | pyproject |
| Test runner | `uv run pytest ...` — never bare `pytest` or `pip` | Global convention |
| `discography/__init__.py` content | Empty | Conflict Resolution |
| Files forbidden this sprint | `spotify_cli/discography/commands.py`, `tests/discography/test_commands.py`, any `main.py` edit | Deferred to Sprint-04 (E2-S3/E2-S4) |
