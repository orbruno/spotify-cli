# Product Backlog - Spotify CLI

**Last Updated**: 2026-06-08
**Stage**: Implementation
**Sprint**: Sprint-02 (✅ complete) — next: Sprint-03 (EP-002 starts)

---

## Epic Roadmap

Visual dependency flow for the project:

### Phase 1: Foundation
- **EP-001: Authentication & Setup** (10 pts) - ✅ Done
  - Depends on: None
  - Blocks: EP-002, EP-003

### Phase 2: Data Access
- **EP-002: Discography Browse** (16 pts) - ⏳ To Do
  - Depends on: EP-001
  - Blocks: EP-003

### Phase 3: Core Feature
- **EP-003: Playlist Creation** (19 pts) - ⏳ To Do
  - Depends on: EP-001, EP-002
  - Blocks: None

**Critical Path**: EP-001 → EP-002 → EP-003

---

## Backlog Summary

### By Epic

| Epic | Stories | Points | Complete | Status |
|------|---------|--------|----------|--------|
| EP-001: Authentication & Setup | 4 | 10 | 100% | ✅ Done |
| EP-002: Discography Browse | 4 | 16 | 0% | ⏳ To Do |
| EP-003: Playlist Creation | 5 | 19 | 0% | ⏳ To Do |
| **Total** | **13** | **45+** | **22%** | - |

### By Priority

- **High Priority**: EP-001 stories (auth login, auth status, auth logout)
- **High Priority**: EP-002 stories — E2-S1 (cache module), E2-S2 (fetcher), E2-S3 (discography command)
- **Medium Priority**: EP-002 — E2-S4 (discography tests)
- **High Priority**: EP-003 stories — E3-S1 (input parser), E3-S2 (batch), E3-S3 (resolver), E3-S4 (commands)
- **Medium Priority**: EP-003 — E3-S5 (playlist tests)

---

## Detailed Backlog

### EP-001: Authentication & Setup

Implements PKCE OAuth 2.0 flow for Spotify. Ref: [SPEC-001](../../_Design/04_Specs/SPEC-001__auth-login.md). Epic: [E1_Authentication-Setup](../Epics/E1_Authentication-Setup.md).

| ID | Story | Priority | Points | Status |
|----|-------|----------|--------|--------|
| [E1-S1](../Stories/E1-S1_Project-Scaffold.md) | Project Scaffold — pyproject.toml, package structure, Typer entry point | High | 2 | ✅ Done |
| [E1-S2](../Stories/E1-S2_Spotify-Client-Factory.md) | Spotify Client Factory — shared SpotifyPKCE factory, CACHE_PATH, env var guard | High | 2 | ✅ Done |
| [E1-S3](../Stories/E1-S3_Auth-Login-Command.md) | Auth Login Command — PKCE browser flow, --no-browser headless mode | High | 3 | ✅ Done |
| [E1-S4](../Stories/E1-S4_Auth-Status-Logout-Tests.md) | Auth Status & Logout + Tests — status/logout commands, full TC-01–TC-08 test suite | High | 3 | ✅ Done |

**Epic Total**: 10 points

---

### EP-002: Discography Browse

Fetches and caches artist track catalogues from Spotify. Ref: [SPEC-002](../../_Design/04_Specs/SPEC-002__discography-browse.md). Epic: [E2_Discography-Browse](../Epics/E2_Discography-Browse.md).

| ID | Story | Priority | Points | Status |
|----|-------|----------|--------|--------|
| [E2-S1](../Stories/E2-S1_Cache-Module.md) | Cache Module — file-based discography cache with 24h TTL | High | 3 | ⏳ To Do |
| [E2-S2](../Stories/E2-S2_Fetcher-Module.md) | Fetcher Module — artist lookup, album pagination, track yield generator | High | 5 | ⏳ To Do |
| [E2-S3](../Stories/E2-S3_Discography-Command.md) | Discography Command — Typer entrypoint, NDJSON streaming, structured errors | High | 5 | ⏳ To Do |
| [E2-S4](../Stories/E2-S4_Discography-Tests.md) | Discography Tests — full test suite for cache, fetcher, and command | Medium | 3 | ⏳ To Do |

**Epic Total**: 16 points

---

### EP-003: Playlist Creation

Full end-to-end playlist creation flow from structured input. Ref: [SPEC-003](../../_Design/04_Specs/SPEC-003__playlist-create.md). Epic: [E3_Playlist-Creation](../Epics/E3_Playlist-Creation.md).

| ID | Story | Priority | Points | Status |
|----|-------|----------|--------|--------|
| [E3-S1](../Stories/E3-S1_Input-Parser.md) | Input Parser — detect & validate stdin / `--uri` / `--file` sources | High | 3 | ⏳ To Do |
| [E3-S2](../Stories/E3-S2_Batch-Module.md) | Batch Module — chunk URIs into 100-item groups and POST to Spotify | High | 3 | ⏳ To Do |
| [E3-S3](../Stories/E3-S3_Search-Resolver.md) | Search Resolver — resolve tracks without URI via Spotify search | High | 2 | ⏳ To Do |
| [E3-S4](../Stories/E3-S4_Playlist-Commands.md) | Playlist Commands — `create`, `add-tracks`, `create-and-add` Typer commands | High | 8 | ⏳ To Do |
| [E3-S5](../Stories/E3-S5_Playlist-Tests.md) | Playlist Tests — full test suite covering all input modes and error paths | Medium | 3 | ⏳ To Do |

**Epic Total**: 19 points

---

## Sprint Roadmap

| Sprint | Epic | Stories | Points | Goal | Status |
|--------|------|---------|--------|------|--------|
| Sprint-01 | E1 | E1-S1, E1-S2 | 4 | Project scaffold + client factory | ✅ Complete |
| Sprint-02 | E1 | E1-S3, E1-S4 | 6 | Full auth command suite + tests | ✅ Complete |
| Sprint-03 | E2 | E2-S1, E2-S2 | 8 | Cache + fetcher | Planned |
| Sprint-04 | E2 | E2-S3, E2-S4 | 8 | Discography command + tests | Planned |
| Sprint-05 | E3 | E3-S1, E3-S2, E3-S3 | 8 | Playlist pipeline (input/batch/resolver) | Planned |
| Sprint-06 | E3 | E3-S4, E3-S5 | 11 | Playlist commands + tests | Planned |
| **Total** | | **13 stories** | **45** | | |

**Sprint backlogs**: See `../Sprints/` for individual sprint backlog files.
**Master overview**: See `../Sprints/sprint-planning-overview.md` for full roadmap and capacity notes.

---

## Tech Debt / Spec Corrections

| ID | Item | Priority | Notes |
|----|------|----------|-------|
| TD-001 | Patch SPEC-001 §1.10 & §3.4 — remove `SPOTIFY_CLIENT_SECRET` from required env vars | Low | PKCE only needs `SPOTIFY_CLIENT_ID` (per ADR-001). Current wording is misleading for new contributors. Code already correct (`require_client_id()` only checks CLIENT_ID). Flagged in Sprint-02 plan; defer to a docs-only sweep. |

---

## Status Legend

- Complete
- In Progress
- Backlog (not started)
- On Hold
- Cancelled

---

## Definition of Done (Story-Level)

For a story to be marked "Done":
- [ ] Code implemented following conventions (Python, Typer, uv)
- [ ] All acceptance criteria met
- [ ] Tests written and passing (`uv run pytest`)
- [ ] Self-reviewed
- [ ] Documentation updated (docstrings, SKILL.md if applicable)
- [ ] Integrated with main codebase
- [ ] No known bugs or issues
- [ ] JSON output validated; exit codes verified

---

**Last Updated**: 2026-06-08
**Next Action**: Run `scrum-sprint-plan` for Sprint-03 (EP-002 — E2-S1 Cache Module + E2-S2 Fetcher Module)
