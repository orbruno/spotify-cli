# Sprint-01 Backlog — Spotify CLI

**Sprint Goal**: Running `uv run spotify-cli --help` works, `SpotifyPKCE` client factory is wired up with `CACHE_PATH`, and `require_client_id()` guard is in place.
**Start**: 2026-06-05 | **End**: TBD | **Status**: ⏳ Planned

---

## Story Board

| Story | Title | Pts | Status | Notes |
|-------|-------|-----|--------|-------|
| E1-S1 | Project Scaffold — pyproject.toml, package structure, Typer entry point | 2 | ⏳ Planned | Creates entire codebase from scratch; no prior baseline |
| E1-S2 | Spotify Client Factory — shared SpotifyPKCE factory, CACHE_PATH, env var guard | 2 | ⏳ Planned | Fills in `core/spotify_client.py` stub; adds TC-02 test |

**Points**: 0 / 4 completed

---

## Execution Order

```
Wave 0  │  pyproject.toml + package skeleton + main.py (E1-S1)
         │  Prerequisite for all imports and entry point
         │
Wave 1  │  E1-S2 ─── Spotify Client Factory
(seq)    │  Fills core/spotify_client.py: CACHE_PATH, SCOPES, REDIRECT_URI,
         │  get_auth_manager(), require_client_id() + TC-02 test
         │
Wave 2  │  Integration verification (no code changes)
         │  uv run spotify-cli --help && uv run spotify-cli -h &&
         │  uv run spotify-cli auth --help && uv run spotify-cli auth -h &&
         │  uv run spotify-cli auth login --help && uv run spotify-cli auth login -h
         │  uv run pytest -x -q --no-cov exits 0
```

---

## Daily Progress

| Date | Outcome |
|------|---------|
| [To be filled during sprint] | |

---

## Blockers

- [ ] `uv` must be installed and available on `$PATH`
- [ ] `SPOTIFY_CLIENT_ID` env var should be set in the shell session (warn if missing, do not block Wave 0/Wave 1 — only needed for integration smoke test)
- [ ] Spotify developer app must have `http://127.0.0.1:9090/callback` registered (needed for E1-S3, not Sprint-01)

---

## Points Tracker

| Wave | Stories | Pts | Done |
|------|---------|-----|------|
| Wave 0 | E1-S1 (scaffold) | 2 | 0 |
| Wave 1 | E1-S2 (client factory) | 2 | 0 |
| Wave 2 | Integration verification | — | — |
| **Total** | | **4** | **0** |
