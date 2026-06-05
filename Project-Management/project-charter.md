# Project Charter - Spotify CLI

**Client**: Solo (personal project)
**Duration**: 2026-06-04 - TBD
**Developer**: Orlando Bruno (Solo)

---

## Vision & Goal

**Problem**: Creating a curated Spotify playlist from a natural-language prompt currently requires 10–15 minutes of manual track searching in the Spotify UI. Spotify's November 2024 removal of the recommendations and audio_features APIs eliminated the programmatic discovery pathway. LLMs have better music curation knowledge than Spotify's own removed discovery engine.

**Solution**: A Python CLI tool that allows AI agents to create Spotify playlists programmatically. The CLI exposes authentication, discography browsing, and playlist creation as agent-invocable commands with JSON I/O and semantic exit codes.

**Success**:
- Zero manual steps from Claude prompt to saved Spotify playlist
- Reliable agent-invocable CLI with JSON I/O and semantic exit codes
- Personal-use tool, no multi-user scope required

---

## Key Stakeholders

- **Developer** (Builder & End User) - Orlando Bruno
- **End Users** - Orlando Bruno and AI agents (Claude) acting on his behalf

---

## Deliverables & Milestones

| Milestone | Due Date | Deliverable |
|-----------|----------|-------------|
| Authentication | TBD | `spotify-cli auth login` — PKCE authentication (SPEC-001) |
| Discography Browse | TBD | `spotify-cli discography` — artist track catalogue with cache (SPEC-002) |
| Playlist Creation | TBD | `spotify-cli playlist create-and-add` — full playlist creation flow (SPEC-003) |
| Agent Onboarding | TBD | `SKILL.md` — agent onboarding document (NFR-16) |

---

## Constraints

- **Timeline**: Personal project, no hard deadline
- **Resources**: Solo developer (Orlando Bruno); no budget constraints
- **Technical**:
  - Spotify Premium required on developer account
  - 5-user Development Mode cap (Spotify API)
  - `localhost` banned as redirect URI — must use `127.0.0.1`
  - Stack: Python, spotipy ≥2.25.1, Typer, uv
- **Scope**: Personal-use only; no multi-user support, no GUI, no playback control, no playlist editing

---

## Out of Scope

- Track discovery / audio analysis / BPM filtering
- Graphical user interface
- Multi-user support
- Playback control
- Playlist editing (post-creation)

---

## Assumptions & Risks

**Assumptions**:
- Spotify Web API remains accessible under the current PKCE OAuth 2.0 flow
- spotipy ≥2.25.1 maintains backward compatibility with the used endpoints
- Claude (or any invoking agent) can parse JSON stdout reliably

**Risks**:
- **[Risk 1 — API changes]** → Mitigation: [Define here]
- **[Risk 2 — Auth token expiry]** → Mitigation: [Define here]
- **[Risk 3 — Rate limiting]** → Mitigation: [Define here]

---

## Definition of Done (Project-Level)

Project is complete when:
- [ ] `spotify-cli auth login` completes PKCE flow and persists token (SPEC-001)
- [ ] `spotify-cli discography` returns paginated artist track list with cache (SPEC-002)
- [ ] `spotify-cli playlist create-and-add` creates playlist and adds tracks end-to-end (SPEC-003)
- [ ] All commands output valid JSON to stdout and use semantic exit codes
- [ ] `SKILL.md` written and tested with a real Claude invocation (NFR-16)
- [ ] All code and documentation committed and pushed to version control

---

**Created**: 2026-06-04
**Last Updated**: 2026-06-04 by Orlando Bruno
