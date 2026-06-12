# Sprint-03: Discography Data Layer (Cache + Fetcher)

**Goal**: The codebase can resolve an artist name, paginate their full album catalogue, stream flat track dicts as a generator, and cache results to disk with a 24h TTL — the complete data layer that the `discography` command (Sprint-04) will orchestrate.

**Status**: ✅ Complete
**Start**: 2026-06-11
**Developer**: Orlando Bruno

---

## Committed Stories

| Story | Title | Epic | Pts |
|-------|-------|------|-----|
| E2-S1 | Cache Module — file-based discography cache with 24h TTL | EP-002 | 3 |
| E2-S2 | Fetcher Module — artist lookup, album pagination, track yield generator | EP-002 | 5 |

**Total committed**: 8 pts

---

## Sprint Notes

- **Layout**: standard single-root. PM artifacts at `Project-Management/`, code/test commands run from the repo root, design docs at `_Design/`.
- **Builds on**: Sprint-02 (auth suite complete, 14 tests green). Sprint-02 PR (#1, `sprint/2026-W23`) is not yet merged — the Sprint-03 branch stacks on top of it.
- **Wave 0 architecture fix (from architecture consult)**: SPEC-002 and stories E2-S3/E2-S4 assume `spotify_cli/auth/spotify_client.py` exposing `get_spotify_client()` and `NotAuthenticatedError` — **neither exists**. The auth client lives at `spotify_cli/core/spotify_client.py`. Wave 0 adds both symbols to `core/spotify_client.py` (canonical location). Sprint-04's E2-S3 must import `from spotify_cli.core.spotify_client import get_spotify_client, NotAuthenticatedError`.
- **429 retry contract**: stories say "up to 3 retries with `Retry-After` (default 1s)"; SPEC-002 §3.1 says "a single retry is sufficient for MVP". Resolution: **3 retries** (stories + sprint stub agree; spec note is stale). Wrap `sp.artist_albums()` and `sp.album_tracks()`; `sp.next()` is not wrapped (out of story scope).
- **`clear()` vs `invalidate()`**: SPEC-002 §2.4 names `invalidate(artist_id)`; story E2-S1 specifies `clear()` (remove all). Implement **`clear()` only** — neither is on the EP-002 critical path; SPEC drift noted for the docs sweep.
- **`discography/__init__.py` stays empty** — SPEC-002 §2.1's "exports DiscographyFetcher" is a fabricated symbol (fetcher is module-level functions). `from spotify_cli.discography import cache` resolves submodules without re-exports.
- **Test conventions**: `unittest.mock` only (pytest-mock is **not** a dependency — story E2-S2's `mocker` fixture example must not be followed). Cache tests redirect `monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)`. No live API calls; no env vars required.
- **No new dependencies**: `spotipy>=2.25.1`, `typer>=0.12.0`, `pytest`, `pytest-cov` already present. No `[tool.pytest.ini_options]` addopts configured — plain pytest commands work.
- **Deferred**: E2-S3 (Discography Command) and E2-S4 (Discography Tests) stay in Sprint-04 — E2-S3 needs the auth contract exercised end-to-end and E2-S4's 80% coverage gate requires `commands.py` to exist.
- **Docs debt carried**: SPEC-002 §1.3 token-cache path wording (`~/.config/spotify-cli/.cache`, not `cache/token.json`); TD-001 (SPEC-001 CLIENT_SECRET wording).

---

## Definition of Done (Sprint Level)

- [x] `uv run pytest tests/ -q` exits 0 (full suite — 39 passed: 14 baseline + 2 Wave 0 + 8 cache + 15 fetcher)
- [x] `uv run pytest tests/discography/test_cache.py -v` exits 0
- [x] `uv run pytest tests/discography/test_fetcher.py -v` exits 0
- [x] `uv run python -c "from spotify_cli.core.spotify_client import get_spotify_client, NotAuthenticatedError"` exits 0
- [x] `uv run python -c "from spotify_cli.discography import cache, fetcher"` exits 0
- [x] `uv run python -c "from inspect import isgeneratorfunction; from spotify_cli.discography.fetcher import iter_tracks; assert isgeneratorfunction(iter_tracks)"` exits 0
- [x] `uv run spotify-cli --help` exits 0 (CLI not broken)
- [x] No test touches the real home directory or the live Spotify API

---

**PR**: [#2 — Sprint 2026-W24: discography data layer](https://github.com/orbruno/spotify-cli/pull/2) (draft, stacked on `sprint/2026-W23`)
**Branch**: `sprint/2026-W24`
**Execution plan**: [autonomous-execution-plan.md](autonomous-execution-plan.md)
