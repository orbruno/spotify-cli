# Spotify CLI — Product Requirements Document

**Version**: 0.1
**Created**: 2026-06-02
**Author**: Orlando Bruno
**Status**: Draft
**Document Type**: PRD (precedes `/sdd:research`, `/sdd:adr`, `/sdd:spec`)

---

## 1. Problem Statement

Spotify removed its `/recommendations` and `/audio_features` endpoints in November 2024, eliminating the primary programmatic path for curated playlist creation. This left a gap: the only reliable way to build a playlist from a conceptual prompt (e.g., "melancholic 70s country road trip") is to search for tracks manually in the Spotify UI.

LLMs (Claude, GPT-4o, etc.) now have substantially better music knowledge than Spotify's own discovery engine for well-known catalogues. A model can generate a high-quality, contextually appropriate track list from a natural-language prompt in seconds. The missing piece is a reliable, scriptable bridge between LLM output and the Spotify API.

No good open-source solution exists for this in 2026. `spotify-web-api-node` was archived in May 2026; `rspotify` is in maintenance mode with no active development. The only existing tools are either abandoned, undocumented, or written for interactive use rather than agent invocation.

**Why now**: The November 2024 API removals created the gap. The quality and availability of LLMs in 2026 make filling that gap viable. The developer has active use for this tool today and is blocked by the manual workaround each time he wants to generate a playlist from a Claude session.

---

## 2. Goals & Success Metrics

### Goals

- Enable the developer to go from a natural-language playlist prompt in Claude to a saved Spotify playlist without any manual steps in the Spotify UI.
- Provide AI agents with a reliable, structured CLI interface for playlist creation that can be invoked as a subprocess and parsed programmatically.
- Eliminate the current workaround of manually searching and adding tracks one by one in the Spotify desktop client.

### Success Metrics

#### Impact Metrics

| Metric | Baseline | Target | Timeframe |
|--------|----------|--------|-----------|
| Time from playlist concept to Spotify playlist saved | ~10–15 min (manual) | Under 60 seconds end-to-end | On first working release |
| Manual steps required after issuing a Claude prompt | 10–20 (search + add per track) | 0 | On first working release |

#### Usage Metrics

| Metric | Target | Timeframe |
|--------|--------|-----------|
| Successful end-to-end playlist creation (auth → search → create → add tracks) without errors | 100% of invocations on valid input | Within v1 |
| Token cache hit rate (silent re-auth on subsequent runs) | 100% within token TTL | Within v1 |
| Structured JSON output parseable by consuming agent without post-processing | 100% of stdout | Within v1 |

---

## 3. Non-Goals

The following are explicitly out of scope for v1. Stating them here prevents scope creep during AI-assisted implementation.

- **Track discovery**: The CLI does not suggest, discover, or recommend tracks. Spotify removed its `/recommendations` API in November 2024. The LLM supplies the track list; the CLI only resolves and writes it.
- **Audio analysis and filtering**: The `/audio_features` endpoint (tempo, energy, danceability, key, etc.) was also removed in November 2024. No BPM, mood, or energy filtering.
- **Multi-user support**: Spotify's Development Mode is capped at 5 authorized users. This is a personal-use, single-account tool. No user management, no invitation flow, no shared playlists.
- **GUI or web interface**: CLI only. No TUI, no web UI, no desktop app.
- **Cross-platform music matching**: No Apple Music, Tidal, or YouTube Music integration in v1. ISRC identifiers are available for future cross-platform work but are deferred.
- **Podcast, audiobook, or episode support**: Music tracks in playlists only. No non-music content types.
- **Playback control**: The CLI writes to the user's Spotify library. It does not play, pause, skip, queue, or otherwise control Spotify playback.
- **Playlist editing**: v1 supports creating new playlists and adding tracks. Updating, reordering, or replacing tracks in existing playlists is deferred (see Open Questions).

---

## 4. Target User / Personas

### Primary User — Orlando Bruno (developer, personal use)

**Who**: Senior software engineer, comfortable with CLIs, OAuth flows, and agentic AI tooling. Runs macOS on Apple Silicon. Uses Claude Code as a daily driver for development work.

**Current behavior**: When he wants a curated playlist, he asks Claude to suggest tracks, then manually searches for each one in the Spotify desktop client and adds them to a new playlist. This takes 10–15 minutes and breaks the flow of the AI session.

**Goals**: Issue a single natural-language prompt to Claude and have a ready-to-play Spotify playlist appear within the same session, with no UI interaction.

**Context of use**: Terminal inside Claude Code sessions on macOS. Invoked interactively during development or creative sessions. Occasionally invoked from shell scripts.

**Technical proficiency**: Can configure OAuth credentials, set environment variables, read JSON output, and debug API errors without hand-holding.

### Secondary User — AI Agents / LLMs Invoking the CLI as a Tool

**Who**: Claude, GPT-4o, or any LLM-based agent that calls the CLI as a subprocess via a tool definition or shell execution step.

**Goals**: Resolve artist + track name pairs to Spotify URIs, create playlists, and add tracks — all without human intervention in the loop.

**Context of use**: Called programmatically; reads stdout for structured results; reads stderr for human-readable errors; checks exit codes for success/failure. Does not interact with a terminal. Requires env-var-based auth (no interactive prompts).

**Technical proficiency**: Not applicable — the agent parses output, not UX.

---

## 5. User Stories

### Story 1: First-Time Authentication

> **As a** developer setting up the CLI for the first time,
> **I want to** authenticate with my Spotify account via a browser login,
> **so that** my credentials are cached and I don't need to authenticate again on future runs.

**Acceptance criteria**:
- [ ] Running any command for the first time opens a browser to the Spotify OAuth authorization URL.
- [ ] After granting permission, the browser redirects to `http://127.0.0.1:{port}/callback` and the CLI captures the authorization code automatically.
- [ ] Tokens are written to `~/.config/spotify-cli/.cache` with file permissions 600.
- [ ] Subsequent runs within the token TTL do not open a browser.
- [ ] When the access token expires, the CLI silently refreshes it using the cached refresh token without user interaction.

### Story 2: Search for a Track

> **As a** developer (or an AI agent acting on my behalf),
> **I want to** search Spotify by artist name and track title,
> **so that** I can confirm the exact canonical track before adding it to a playlist.

**Acceptance criteria**:
- [ ] Given a valid artist name and track title, the CLI returns a JSON object containing the canonical track name, artist name, album name, and Spotify URI.
- [ ] If no match is found, the CLI returns a structured JSON error on stdout and exits with a non-zero code.
- [ ] The JSON output is valid and parseable without post-processing.

### Story 3: Create a Playlist and Add Tracks

> **As a** developer running a Claude session,
> **I want to** create a new Spotify playlist and populate it with a list of track URIs in a single workflow,
> **so that** the playlist is ready to play without any manual steps in the Spotify UI.

**Acceptance criteria**:
- [ ] Given a playlist name, optional description, and visibility flag, the CLI creates the playlist on the authenticated user's account and returns the playlist URI and URL as JSON.
- [ ] Given a playlist ID and a list of track URIs, the CLI adds all tracks, batching requests at 100 URIs per API call.
- [ ] The CLI outputs a confirmation payload listing the canonical track names that were added.
- [ ] The entire flow (create + add) completes without prompting the user for input unless `--confirm` is passed.

### Story 4: Browse an Artist's Discography

> **As a** developer or AI agent,
> **I want to** retrieve all albums and tracks for a given artist with their Spotify URIs,
> **so that** I can select from verified URIs rather than guessing track names.

**Acceptance criteria**:
- [ ] Given an artist name, the CLI returns a paginated, complete list of albums with tracks and Spotify URIs.
- [ ] Results can be filtered by `album_type` (album, single, compilation) and `release_date` range.
- [ ] All pagination is handled transparently — the full discography is returned in a single response.
- [ ] Output is valid JSON.

### Story 5: Headless Agent Authentication

> **As a** an AI agent running in a headless environment,
> **I want to** authenticate without a browser being opened automatically,
> **so that** the CLI can be used in non-interactive contexts.

**Acceptance criteria**:
- [ ] When `--no-browser` is passed, the CLI prints the authorization URL to stdout rather than opening a browser.
- [ ] The CLI accepts the redirect URL via stdin and completes the token exchange.
- [ ] All subsequent behavior is identical to interactive authentication.

---

## 6. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | The system shall authenticate a user via OAuth 2.0 PKCE on first run by opening a browser and capturing the redirect on `http://127.0.0.1:{port}/callback`. | High |
| FR-02 | The system shall silently refresh the access token on subsequent runs using the cached refresh token, without requiring browser interaction. | High |
| FR-03 | Given an artist name and track title, the system shall return the canonical Spotify track name, artist, album, and URI as JSON. | High |
| FR-04 | Given an artist name, the system shall return a paginated list of all albums and their tracks with Spotify URIs. | High |
| FR-05 | The system shall create a new Spotify playlist with a given name, description, and public/private visibility on the authenticated user's account. | High |
| FR-06 | The system shall add a list of track URIs to a playlist in batches of up to 100 per API call. | High |
| FR-07 | The system shall output all results as JSON on stdout by default, suitable for consumption by an AI agent subprocess call. | High |
| FR-08 | The system shall return a confirmation payload (resolved canonical track list) before writing to a playlist when `--confirm` flag is used. | Medium |
| FR-09 | The system shall support a `--no-browser` flag for headless environments, printing the auth URL to stdout and accepting the redirect URL via stdin. | Medium |
| FR-10 | The system shall filter discography results by `album_type` (album, single, compilation) and `release_date` range. | Medium |
| FR-11 | The system shall support a `--page-all` flag on list/discography commands that streams all paginated results as NDJSON (one JSON object per line) to stdout, in addition to the default single-page response. | Medium |
| FR-12 | All mutation commands (playlist create, tracks add) shall support a `--dry-run` flag that prints the would-be operation as a JSON payload to stdout and exits 0 without executing the write. | Medium |
| FR-13 | Mutation commands that are irreversible (playlist delete, track removal) shall require an explicit `--yes` flag; invoking without `--yes` shall exit 2 with a JSON error on stderr. | Medium |
| FR-14 | The system shall accept a `--format` flag with value `json` (default) to allow explicit output mode selection; reserved for future format additions without breaking existing consumers. | Low |
| FR-15 | The system shall cache discography responses at `~/.config/spotify-cli/cache/discography/{artist_id}.json` with a default TTL of 24 hours. A `--no-cache` flag shall bypass the cache for any command. A `spotify-cli cache clear` subcommand shall delete all cached files. | Medium |

---

## 7. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Security | OAuth tokens stored at `~/.config/spotify-cli/.cache` with file permissions 600. No tokens written to stdout or logs. |
| NFR-02 | Security | Client ID and client secret read from environment variables `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` respectively — never hardcoded or written to logs. |
| NFR-03 | Reliability | On Spotify API 429 response, the system shall retry after the `Retry-After` header value with exponential backoff, up to 3 retries before returning a structured error. |
| NFR-04 | Reliability | The system shall handle paginated Spotify responses transparently, fetching all pages before returning results to the caller. |
| NFR-05 | Usability | All commands shall produce valid, parseable JSON on stdout. Human-readable error messages shall be written to stderr only, never mixed into stdout. |
| NFR-06 | Portability | The tool shall run on macOS (primary target) and Linux (secondary) without modification. |
| NFR-07 | Packaging | The tool shall be distributed and installable via `uv` / `uvx`. No pip, no bare python invocation. |
| NFR-08 | Output | The system shall strip all ANSI escape codes from stdout when stdout is not a TTY (i.e., when output is piped). The `NO_COLOR` environment variable shall suppress all ANSI output regardless of TTY state. Animations and spinners shall be written exclusively to stderr. |
| NFR-09 | Reliability | The system shall use semantic exit codes: 0 = success; 1 = general operation failure; 2 = argument misuse or missing required flag; 3 = input validation error; 4 = Spotify API domain error (e.g., resource not found, permission denied). Exit codes shall never be inferred from stdout content. |
| NFR-10 | Usability | All commands shall produce `--help` output generated by the CLI framework (Typer/Click). Help text shall begin with a `Usage:` line followed by at least one concrete `Example:` block. Help shall be displayed automatically when a command is invoked with no required arguments. `-h` shall be equivalent to `--help`. No decorative borders, emoji, or colour in help body text. |
| NFR-11 | Usability | The CLI shall generate shell completion scripts for bash, zsh, and fish via a `spotify-cli completion <shell>` subcommand or equivalent framework-generated mechanism. |
| NFR-12 | Usability | The CLI shall expose a `--version` flag at the root level that prints the current version string to stdout and exits 0. |
| NFR-13 | Usability | The system shall resolve configuration values in the following precedence order (highest to lowest): explicit CLI flag, environment variable, config file at `~/.config/spotify-cli/config.toml`, built-in default. All configuration keys available as flags shall also be settable via environment variables with the prefix `SPOTIFY_CLI_`. |
| NFR-14 | Security | All string inputs (track names, playlist names, artist names, IDs) shall be validated before use: null bytes and ANSI injection sequences shall be rejected with exit code 3. File path inputs shall reject path traversal sequences (`../`). User-supplied strings shall never be passed to shell execution. |
| NFR-15 | Observability | All errors written to stderr shall follow a structured JSON anatomy: `{ "error": "<what failed>", "reason": "<why>", "suggestion": "<how to fix>", "help": "<command --help reference>" }`. Human-readable prose errors are not acceptable on stderr in non-TTY contexts. |
| NFR-16 | Agent Integration | The repository shall ship a `SKILL.md` file at the project root that serves as the agent onboarding document: one-paragraph summary, installation, authentication, common operations with examples, and exit codes. `SKILL.md` shall remain under 2,500 tokens. |
| NFR-17 | Agent Integration | Before v1.0 release, an agent smoke test shall be run: provide Claude with only `SKILL.md` and `--help` output, then ask it to complete a 3-step task (search → create playlist with `--dry-run` → confirm and execute). The CLI is not shippable if this test fails due to unclear output or missing flags. |
| NFR-18 | Performance | The CLI startup time (time-to-first-output for a `--help` invocation) shall not exceed 500ms on the primary target platform (macOS Apple Silicon). For scripting-critical invocations (non-TTY), startup shall be measured and documented. |

---

## 8. Assumptions & Dependencies

### Assumptions

- The developer maintains an active Spotify Premium subscription. The Spotify Web API requires Premium for certain scopes; if the subscription lapses, playlist write operations will fail.
- The Spotify app is registered at `developer.spotify.com` with redirect URI set to `http://127.0.0.1:{port}/callback`. Spotify banned `localhost` as a redirect URI in November 2025; `127.0.0.1` is the required form.
- This tool is personal-use only with no intention to submit for Spotify's extended access / quota extension program. Development Mode (≤ 5 authorized users) is sufficient.
- The LLM invoking the CLI has sufficient music knowledge to generate valid artist + track name pairs for well-known catalogues. The CLI resolves and validates them, but the LLM is the source of the initial list.

### Dependencies

- `spotipy ≥ 2.25.1` — Spotify Web API Python client. Version 2.25.1 or later required for PKCE support and the CVE-2025-27154 fix that sets correct file permissions on the token cache.
- `typer` — CLI framework for command definition and argument parsing.
- `uv` — Package manager for installation and distribution. No pip or bare python.
- Spotify Developer Account with a registered application and the redirect URI configured as described above.
- Active Spotify Premium subscription on the developer account used for authentication.

---

## 9. Open Questions

| Question | Owner | Resolution by | Status |
|----------|-------|---------------|--------|
| `--confirm` flag: opt-in or opt-out? Resolved: opt-in. Agents get fast default writes; humans pass `--confirm` explicitly. | Orlando Bruno | 2026-06-03 | Resolved |
| Cache discography results locally? Resolved: yes — file cache at `~/.config/spotify-cli/cache/`, 24h TTL, `--no-cache` to bypass. | Orlando Bruno | 2026-06-03 | Resolved |
| Playlist editing (update/replace tracks) in v1? Resolved: no — create-new only. Editing deferred to v2. | Orlando Bruno | 2026-06-03 | Resolved |

---

## 10. Related Documents

### Upstream (informs this PRD)

- Research — Auth flows, endpoints, stack decisions: `../02_Research/01_Spotify-API-Playlist-Creation.md`
- Research — Full object model, attributes, removed capabilities: `../02_Research/02_Spotify-API-Objects-Attributes-Capabilities.md`

### Downstream (SDD pipeline — created from this PRD)

- Research: `../02_Research/` *(exploration of options before committing)*
- ADR: `../03_ADR/` *(architectural decisions made for this product)*
- Spec: `../04_Specs/active/` *(feature-level requirements derived from this PRD)*

---

## Status Log

| Date | Status | Note |
|------|--------|------|
| 2026-06-02 | Draft | Initial scaffold |
| 2026-06-03 | Draft | PRD filled in from session research |
| 2026-06-03 | Draft | Added FR-11–FR-14 and NFR-08–NFR-18 from CLI playbook audit |
| 2026-06-03 | Draft | Resolved all 3 open questions; added FR-15 (discography cache) |

---

**Last Updated**: 2026-06-03 by Orlando Bruno
