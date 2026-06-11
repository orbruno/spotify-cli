# Project Management - Spotify CLI

## Overview

A Python CLI tool that allows AI agents to create Spotify playlists programmatically, bridging the gap left by Spotify's November 2024 removal of the recommendations and audio_features APIs.

**Framework**: SCRUM Solo (adapted for individual work)
**Developer**: Orlando Bruno
**Sprint Duration**: 1 session
**Current Focus**: Sprint-03 planned — discography data layer (cache + fetcher); EP-002 starts

## Structure

```
Project-Management/
├── README.md                     # This file
├── project-charter.md            # Vision, stakeholders, constraints, DoD
├── Backlog/
│   └── Product-Backlog.md        # Prioritized backlog + Epic Roadmap
├── Epics/
│   ├── E1_[Epic-Name].md         # Epic definitions
│   └── ...
├── Stories/
│   ├── E1-S1_[Story-Name].md     # User stories by epic
│   └── ...
├── Sprints/
│   ├── Sprint-01/
│   │   ├── sprint-backlog.md     # Sprint commitment & daily progress
│   │   └── sprint-retrospective.md
│   └── ...
├── Reports/
└── _Archive/                     # Completed or deprecated items
```

## Quick Links

- **Current Sprint**: [Sprints/Sprint-03/sprint-backlog.md](Sprints/Sprint-03/sprint-backlog.md)
- **Product Backlog**: [Backlog/Product-Backlog.md](Backlog/Product-Backlog.md)
- **Project Charter**: [project-charter.md](project-charter.md)

## Current Status

**Active Epic(s)**: EP-002: Discography Browse
**Sprint**: Sprint-03 planned (E2-S1 Cache + E2-S2 Fetcher, 8 pts) — see `Sprints/Sprint-03/autonomous-execution-plan.md`. Sprint-02 manual verification still pending live OAuth; see `Sprints/Sprint-02/manual-verification.md`
**Last Sprint Goal**: ✅ `spotify-cli auth login`, `auth status`, and `auth logout` all work as specified by automated tests; 14/14 pass, 100% coverage of `auth/` and `core/`. Live-OAuth checks (browser launch, cache perms 600, `--no-browser` URL/stdin flow, silent refresh) are tracked separately as manual verification.

### Progress Summary

| Epic | Status | Progress |
|------|--------|----------|
| EP-001: Authentication & Setup | ✅ Done | 100% |
| EP-002: Discography Browse | ⏳ Backlog | 0% |
| EP-003: Playlist Creation | ⏳ Backlog | 0% |

## Getting Started

1. **Understand the vision**: Read `project-charter.md`
2. **See the roadmap**: Check `Backlog/Product-Backlog.md`
3. **Current work**: See `Sprints/Sprint-03/sprint-backlog.md`
4. **Deep dive**: Explore `Epics/` and `Stories/`

## Sprint Cadence

One sprint = one working session. Each session follows:

| Activity | Timing |
|----------|--------|
| Sprint Planning | Session start |
| Development | Session core |
| Sprint Review + Retrospective | Session end |

## Story Pointing Reference

| Points | Complexity | Time |
|--------|------------|------|
| 1 | Trivial | ~1-2h |
| 2 | Simple | ~half day |
| 3 | Moderate | ~1 day |
| 5 | Significant | ~2-3 days |
| 8 | Complex | ~1 week |

## For AI Agents

### Key Context
- This is SCRUM adapted for solo work
- Stories link to parent epics via ID (E1-S1 = Epic 1, Story 1)
- Story points = complexity + uncertainty, not strict time
- Definition of Done in `project-charter.md`
- One sprint = one working session (not a fixed calendar duration)

### When Creating New Artifacts
1. **Epic**: Create in `Epics/EN_Epic-Name.md`, add to Product Backlog
2. **Story**: Create in `Stories/EN-SN_Story-Name.md`, link to epic
3. **Sprint**: Create folder `Sprints/Sprint-NN/` with backlog and retro templates

### Naming Conventions
- Epics: `EN_Name.md` (E1, E2, E3...)
- Stories: `EN-SN_Name.md` (E1-S1, E1-S2...)
- Sprints: `Sprint-NN/` (Sprint-01, Sprint-02...)

---

**Last Updated**: 2026-06-08
**Maintained by**: Orlando Bruno
