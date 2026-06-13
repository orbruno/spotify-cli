# Sprint Planning Overview — Spotify CLI

**Project**: Spotify CLI
**Developer**: Orlando Bruno
**Sprint Length**: 1 session (~2–4 hours focused work)
**Total Scope**: 45 points across 13 stories, 3 epics
**Created**: 2026-06-05

---

## Roadmap

| Sprint | Epic | Stories | Points | Goal | Status |
|--------|------|---------|--------|------|--------|
| Sprint-01 | E1 | E1-S1, E1-S2 | 4 | Project scaffold + client factory | Done |
| Sprint-02 | E1 | E1-S3, E1-S4 | 6 | Full auth command suite + tests | Planned |
| Sprint-03 | E2 | E2-S1, E2-S2 | 8 | Cache + fetcher | Planned |
| Sprint-04 | E2 | E2-S3, E2-S4 | 8 | Discography command + tests | Planned |
| Sprint-05 | E3 | E3-S1, E3-S2, E3-S3 | 8 | Playlist pipeline (input/batch/resolver) | Planned |
| Sprint-06 | E3 | E3-S4, E3-S5 | 11 | Playlist commands + tests | Planned |
| **Total** | | **13 stories** | **45** | | |

---

## Critical Path

```
Sprint-01 (scaffold)
    └── Sprint-02 (auth)
            ├── Sprint-03 (discography data layer)
            │       └── Sprint-04 (discography command)
            └── Sprint-05 (playlist pipeline)
                    └── Sprint-06 (playlist commands)
```

---

## Sprint Details

### Sprint-01 — Project Scaffold + Client Factory
**Points**: 4 | **Status**: Done | **Date**: 2026-06-05
**Stories**: E1-S1 (2 pts), E1-S2 (2 pts)
**Deliverables**:
- `uv run spotify-cli --help` and `--version` work
- Package skeleton with all `__init__.py` and stub files in place
- `core/spotify_client.py` with `CACHE_PATH`, `require_client_id()`, and `get_auth_manager()`
- TC-02 unit test passing (missing `SPOTIFY_CLIENT_ID` → exit 2)

### Sprint-02 — Full Auth Command Suite + Tests
**Points**: 6 | **Status**: Planned | **Dependency**: Sprint-01
**Stories**: E1-S3 (3 pts), E1-S4 (3 pts)
**Deliverables**:
- `auth login` — PKCE browser flow; `--no-browser` headless mode
- `auth status` — valid/expired/missing token states
- `auth logout` — idempotent cache deletion
- TC-01 through TC-08 from SPEC-001 all passing
- Coverage ≥80% for `spotify_cli/auth` and `spotify_cli/core`

### Sprint-03 — Cache + Fetcher Modules
**Points**: 8 | **Status**: Planned | **Dependency**: Sprint-02
**Stories**: E2-S1 (3 pts), E2-S2 (5 pts)
**Deliverables**:
- `discography/cache.py` — 24h TTL, atomic writes, miss/hit/expiry/corruption handling
- `discography/fetcher.py` — artist lookup, album pagination, track generator, 429 retry
- Unit tests for both modules passing

### Sprint-04 — Discography Command + Tests
**Points**: 8 | **Status**: Planned | **Dependency**: Sprint-03
**Stories**: E2-S3 (5 pts), E2-S4 (3 pts)
**Deliverables**:
- `spotify-cli discography "Johnny Cash"` streams NDJSON to stdout
- Cache hit/miss logic, `--no-cache`, `--from-year`, `--to-year`, `--album-type`, `--page-all`
- TC-01 through TC-11 from SPEC-002 passing
- Coverage ≥80% for `spotify_cli/discography`

### Sprint-05 — Playlist Pipeline (Input/Batch/Resolver)
**Points**: 8 | **Status**: Planned | **Dependency**: Sprint-02 (Sprint-04 recommended)
**Stories**: E3-S1 (3 pts), E3-S2 (3 pts), E3-S3 (2 pts)
**Deliverables**:
- `playlist/input_parser.py` — stdin/`--uri`/`--file` modes, mutual exclusivity, URI validation, path traversal check
- `playlist/batch.py` — `ResolvedTrack`, `BatchResult` dataclasses; 100-item chunking; 429 retry; partial failure handling
- `playlist/resolver.py` — URI passthrough + search fallback + no-match marking
- Unit tests for all three modules passing

### Sprint-06 — Playlist Commands + Tests (Final Sprint)
**Points**: 11 | **Status**: Planned | **Dependency**: Sprint-05
**Stories**: E3-S4 (8 pts), E3-S5 (3 pts)
**Deliverables**:
- `playlist create`, `playlist add-tracks`, `playlist create-and-add` commands
- `--dry-run` on both write commands
- TC-01 through TC-14 from SPEC-003 passing
- Coverage ≥80% for `spotify_cli/playlist`
- Full `uv run pytest` green across all modules
- `SKILL.md` written (NFR-16)
- Agent smoke test passed (NFR-17)

---

## Capacity Notes

Sprint length is 1 session (~2–4 hours focused work). Points planned at 60–70% capacity:

| Sprint | Points | Capacity Assessment |
|--------|--------|---------------------|
| Sprint-01 | 4 | Light — good warm-up sprint for setup work |
| Sprint-02 | 6 | Moderate — focused auth implementation |
| Sprint-03 | 8 | Full — two modules, can be worked in parallel order |
| Sprint-04 | 8 | Full — command integration + full test suite |
| Sprint-05 | 8 | Full — three modules, soft chain E3-S1 → E3-S2 → E3-S3 |
| Sprint-06 | 11 | Heavy — may need 2 sessions; split E3-S4 tasks across sessions if needed |

**Sprint-06 split strategy (if 2 sessions needed)**:
- Session A: E3-S4 command implementation + manual smoke test
- Session B: E3-S5 full test suite + coverage gate + `SKILL.md` + agent smoke test

---

## Definition of Done (Project-Level)

- [ ] All 3 epics complete (45 pts)
- [ ] `uv run pytest` green across all modules (≥80% coverage)
- [ ] `spotify-cli auth login` → `discography` → `playlist create-and-add` works end-to-end
- [ ] `SKILL.md` written (NFR-16)
- [ ] Agent smoke test passed (NFR-17): Claude drives CLI using only `SKILL.md` + `--help`

---

## Story Index

| Story ID | Title | Epic | Sprint | Points |
|----------|-------|------|--------|--------|
| E1-S1 | Project Scaffold | EP-001 | Sprint-01 | 2 |
| E1-S2 | Spotify Client Factory | EP-001 | Sprint-01 | 2 |
| E1-S3 | Auth Login Command | EP-001 | Sprint-02 | 3 |
| E1-S4 | Auth Status & Logout + Tests | EP-001 | Sprint-02 | 3 |
| E2-S1 | Cache Module | EP-002 | Sprint-03 | 3 |
| E2-S2 | Fetcher Module | EP-002 | Sprint-03 | 5 |
| E2-S3 | Discography Command | EP-002 | Sprint-04 | 5 |
| E2-S4 | Discography Tests | EP-002 | Sprint-04 | 3 |
| E3-S1 | Input Parser | EP-003 | Sprint-05 | 3 |
| E3-S2 | Batch Module | EP-003 | Sprint-05 | 3 |
| E3-S3 | Search Resolver | EP-003 | Sprint-05 | 2 |
| E3-S4 | Playlist Commands | EP-003 | Sprint-06 | 8 |
| E3-S5 | Playlist Tests | EP-003 | Sprint-06 | 3 |
| **Total** | | | | **45** |

---

**Last Updated**: 2026-06-05 by Orlando Bruno
