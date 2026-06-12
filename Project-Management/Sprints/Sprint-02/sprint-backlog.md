# Sprint-02 Backlog — Spotify CLI

**Sprint Goal**: `spotify-cli auth login`, `auth status`, and `auth logout` all work correctly with structured JSON output; TC-01 through TC-08 from SPEC-001 §2.6 pass with ≥80% coverage.
**Start**: 2026-06-08 | **End**: 2026-06-08 | **Status**: ✅ Done (automated) · ⏳ Manual verification pending — see `manual-verification.md`

---

## Story Board

| Story | Title | Pts | Status | Notes |
|-------|-------|-----|--------|-------|
| E1-S3 | Auth Login Command | 3 | ✅ Done | Fills `login()` stub; adds TC-01 and TC-03; USE `as_dict=False` and `cache_path` in output |
| E1-S4 | Auth Status & Logout + Tests | 3 | ✅ Done | Adds `status()` and `logout()`; writes TC-01–TC-08; USE `"no_session"` not `"no_cache"` |

**Points**: 6 / 6 completed

---

## Execution Order

```
Wave 1  │  E1-S3 ─── Auth Login Command
(seq)   │            (login() impl, TC-01, TC-03)
        │
        │  E1-S4 ─── Auth Status & Logout + Tests
        │            (status(), logout(), TC-01–TC-08 complete suite)
        │
Wave 2  │  Integration verification (no code changes — run and report only)
```

---

## Daily Progress

| Date | Outcome |
|------|---------|
| 2026-06-08 | E1-S3 and E1-S4 implemented. Review round 1 surfaced: `status()` required `SPOTIFY_CLIENT_ID` unnecessarily, `test_silent_refresh` did not test refresh, missing tests (expired token, no-client-id, cached-None), DoD checkboxes marked done without manual verification. Fixed: added `get_cached_token()` helper to decouple cache inspection from Spotipy instantiation; `status()` no longer calls `require_client_id()`; reworked TC-08 to assert `login()` delegates to `get_access_token(as_dict=False)`; added 3 new test cases; PM artifacts now separate automated AC from manual verification (see `manual-verification.md`). Final: 14/14 tests pass, **100% coverage**. Sprint goal met (automated portion); manual verification pending live OAuth. |

---

## Blockers

- [ ] Sprint-01 must be fully merged/on branch (`main.py` + `core/spotify_client.py` + `auth/commands.py` stub) before Wave 1 starts
- [ ] `SPOTIFY_CLIENT_ID` must be available in the development environment for manual verification steps
- [ ] SPEC-001 §1.10 references `SPOTIFY_CLIENT_SECRET` as required — misleading for PKCE; update before or during sprint

---

## Points Tracker

| Wave | Stories | Pts | Done |
|------|---------|-----|------|
| Wave 1 (seq) | E1-S3, E1-S4 | 6 | 6 |
| Wave 2 | Integration verification | — | ✅ |
| **Total** | | **6** | **6** |
