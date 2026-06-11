# Sprint-03 Backlog — Spotify CLI

**Sprint Goal**: The codebase can resolve an artist name, paginate their full album catalogue, stream flat track dicts as a generator, and cache results to disk with a 24h TTL.
**Start**: TBD | **End**: TBD | **Status**: ⏳ Planned

---

## Story Board

| Story | Title | Pts | Status | Notes |
|-------|-------|-----|--------|-------|
| E2-S1 | Cache Module | 3 | ⏳ Planned | Pure stdlib; atomic `.tmp` → `replace()`; `monkeypatch CACHE_DIR` in tests |
| E2-S2 | Fetcher Module | 5 | ⏳ Planned | Generator semantics mandatory; 429 → 3 retries via `_call_with_retry` helper |

**Points**: 0 / 8 completed

---

## Execution Order

```
Wave 0  │  Foundation: discography/tests package __init__ files +
         │  get_spotify_client() / NotAuthenticatedError in core/spotify_client.py
         │
Wave 1  │  E2-S1 ─── Cache Module (cache.py + test_cache.py)
(seq)    │  E2-S2 ─── Fetcher Module (fetcher.py + test_fetcher.py)
         │
Wave 2  │  Integration verification (no code changes — run & report)
```

E2-S1 and E2-S2 share no files (parallel-safe), but run sequentially in autonomous solo mode to avoid git conflicts.

---

## Daily Progress

| Date | Outcome |
|------|---------|
| [To be filled during sprint] | |

---

## Blockers

- [ ] Sprint-02 baseline must be green: `uv run pytest tests/ -x -q` exits 0 (verified at planning: 14 passed)
- [ ] `uv` available on PATH
- [ ] No env vars required — all spotipy calls mocked in tests

---

## Points Tracker

| Wave | Stories | Pts | Done |
|------|---------|-----|------|
| Wave 0 | Foundation (auth contract + package scaffolding) | — | 0 |
| Wave 1 | E2-S1, E2-S2 | 8 | 0 |
| Wave 2 | Integration verification | — | 0 |
| **Total** | | **8** | **0** |

---

**Last Updated**: 2026-06-11
**Status**: ⏳ Planned
