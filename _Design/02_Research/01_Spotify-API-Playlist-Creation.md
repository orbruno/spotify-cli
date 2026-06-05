# Spotify API — Playlist Creation

**Created**: 2026-06-02
**Author**: Orlando Bruno
**Status**: Draft

---

## TL;DR

- **Summary**: The Spotify Web API supports programmatic playlist creation via OAuth 2.0 (PKCE flow), search, and a batch-add endpoint — giving a CLI tool a clean three-step path: authenticate → search for track URIs → create playlist and populate it.
- **Industry/Product relevance**: Spotify removed all algorithmic discovery endpoints (recommendations, audio features, related artists) in November 2024, meaning the API is strictly a write target — the LLM or AI agent must supply the track list; Spotify resolves names to URIs and persists the playlist.
- **Decisions**: Use `spotipy ≥ 2.25.1` with `SpotifyPKCE` and an explicit `cache_path`; redirect URI must be `http://127.0.0.1:{port}/callback` (not `localhost`); tool is personal-use only due to Spotify's 5-user Development Mode cap.

## Context

The Spotify CLI needs to authenticate as a user and create playlists populated with tracks chosen by an AI agent. Before writing any code, this research answers:

1. Which OAuth flow is correct for a desktop/CLI app?
2. Which API endpoints cover the create-playlist workflow?
3. What are the rate limit, scope, and developer account constraints?
4. What library and stack should the project adopt?
5. How does the removal of discovery endpoints change the architecture?

## Findings

### Option A: Authorization Code + PKCE (Recommended)

**Description**: The client generates a `code_verifier`, hashes it to a `code_challenge`, opens a browser to Spotify's auth page, spins up a one-request HTTP server on `http://127.0.0.1:{port}` to catch the redirect, and exchanges the authorization code for access + refresh tokens. No client secret is ever stored. spotipy's `SpotifyPKCE` class handles the full flow when given an explicit `cache_path`.

**Pros**:
- No client secret required — nothing sensitive lives in the binary or config
- Supports refresh tokens — the CLI can operate silently after the first login
- Explicitly documented by Spotify as the correct flow for desktop, CLI, and mobile apps
- spotipy handles PKCE derivation, token exchange, and refresh automatically
- Refresh tokens may rotate; spotipy always writes back whatever the response returns

**Cons**:
- Requires a browser on first run (mitigated by a `--no-browser` headless fallback that prints the URL and accepts a pasted redirect URI)
- One-time setup friction for end users

**Cost/Effort**: Low — spotipy wraps the entire flow; the CLI only needs to expose `auth login` and `auth logout` subcommands.

**Token storage**:
- Store `{access_token, refresh_token, expires_at}` at `~/.config/spotify-cli/.cache`
- File permissions: 600
- On each CLI run: check `expires_at`; if stale, POST to `/api/token` with `grant_type=refresh_token` + `client_id`
- Must set `cache_path` explicitly — spotipy defaults to CWD `.cache`

**Critical redirect URI constraint**: `localhost` is banned as a redirect URI since November 2025. Must use `http://127.0.0.1:{port}/callback`.

---

### Option B: Authorization Code (with client secret)

**Description**: Standard server-side OAuth flow. The client secret is embedded in the app or stored in a config file and sent during token exchange.

**Pros**:
- Simpler conceptually (no PKCE derivation)
- Fully supported by spotipy (`SpotifyOAuth`)

**Cons**:
- Requires storing a client secret on disk — a security liability for a distributed CLI tool
- Not the recommended flow for desktop/CLI apps per Spotify documentation

**Cost/Effort**: Similar to PKCE, but with ongoing secret-management overhead.

---

### Option C: Client Credentials

**Description**: Machine-to-machine flow — no user context. The app authenticates as itself using client ID + secret.

**Pros**:
- Simplest to implement; no browser redirect needed

**Cons**:
- Cannot access any user data — playlist creation and track search against a user's library are impossible
- Does not issue refresh tokens

**Cost/Effort**: N/A — ruled out entirely for this use case.

---

### Library Comparison: spotipy vs. manual HTTP vs. alternatives

**spotipy ≥ 2.25.1 (Python)**:
- Actively maintained (2.26.0 released March 2026)
- `SpotifyPKCE` class handles PKCE + token refresh end-to-end
- `CacheFileHandler` with explicit path resolves the CWD-default issue
- CVE-2025-27154 (token cache file permissions) fixed in ≥ 2.25.1 — version pin is a security requirement
- Integrates cleanly with Typer for a Python CLI

**Manual HTTP (httpx / requests)**:
- Full control, no abstraction overhead
- Requires reimplementing PKCE derivation, token refresh, retry logic, and pagination — high effort for no gain

**Rejected alternatives**:
- `spotify-web-api-node` (JS): archived May 2026
- `rspotify` (Rust): maintenance mode
- `@spotify/web-api-ts-sdk` (TS): viable but Python is preferred for AI agent tooling context

## Comparison

| Criteria | PKCE (Option A) | Auth Code + Secret (Option B) | Client Credentials (Option C) |
|----------|----------------|-------------------------------|-------------------------------|
| User data access | Yes | Yes | No |
| Refresh tokens | Yes | Yes | No |
| Secret on disk | No | Yes | Yes |
| Spotify-recommended for CLI | Yes | No | No |
| spotipy support | `SpotifyPKCE` | `SpotifyOAuth` | `SpotifyClientCredentials` |
| Headless fallback | Yes (`--no-browser`) | Yes | Yes |
| Security posture | Strong | Weak | N/A |

## Key API Endpoints

| Endpoint | Method | Purpose | Scope Required |
|----------|--------|---------|----------------|
| `/me` | GET | Get authenticated user's ID (required before creating playlists) | `user-read-private` |
| `/search?q=...&type=track` | GET | Find tracks by name, artist, album — returns track URIs | None |
| `/me/playlists` | POST | Create a new playlist for the authenticated user | `playlist-modify-public` or `playlist-modify-private` |
| `/playlists/{id}/items` | POST | Add up to 100 track URIs per request (batch) | `playlist-modify-public` or `playlist-modify-private` |

**Deprecated endpoint (do not use)**: `/users/{id}/playlists` for playlist creation was removed in February 2026. Use `/me/playlists`.

**Required scopes**: `playlist-modify-public playlist-modify-private user-read-private`

## Rate Limits

Spotify does not publish official rate limit numbers. Community-observed ceiling: ~180 requests per 30 seconds before 429 responses. Implementation requirement: respect the `Retry-After` header on 429 responses.

For the playlist creation workflow (search N tracks + create 1 playlist + batch-add up to 100 tracks per request), rate limits are not a practical concern at fewer than 100 tracks per invocation.

## Track Discovery Limitation

Spotify removed the following endpoints in November 2024:
- `GET /recommendations` — algorithmic track suggestions
- `GET /audio-features/{id}` — BPM, energy, danceability per track
- `GET /artists/{id}/related-artists`
- `GET /browse/featured-playlists`

**Architectural consequence**: Spotify cannot serve as the track discovery engine. The LLM or AI agent must supply the track list as `{artist, track}` pairs. The CLI's role is purely as a write target: resolve names to URIs via `/search`, then create and populate the playlist.

## Developer Account Constraints (2026)

- **Premium required**: the developer account owner must hold an active Spotify Premium subscription — if it lapses, the app stops working
- **5-user cap in Development Mode**: the app can only be authorized by 5 Spotify accounts (including the developer); no individual path to extended access — that requires a company/organization application
- **App registration**: requires creating an app at `developer.spotify.com` and setting the redirect URI to `http://127.0.0.1:{port}/callback`
- **Practical implication**: this tool is personal-use only

## AI Agent Integration Design

For an LLM agent to invoke this CLI:

- Agent provides: playlist name, description, list of `{artist, track}` pairs
- CLI interface: JSON input via stdin or flags; JSON output for scripting
- Environment variables for headless/CI auth: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CACHE_PATH`
- Exit codes: `0` = success, `1` = auth error, `2` = track not found, `3` = API error

## Recommendation

The recommended approach is **Authorization Code + PKCE via spotipy ≥ 2.25.1** because:

- It is the only flow that combines user-data access, refresh token support, and no stored client secret — the correct security posture for a distributed CLI tool
- spotipy's `SpotifyPKCE` class eliminates all PKCE implementation complexity; the CLI only needs to configure `cache_path` and call `sp.me()` to verify the session
- The stack (Python + spotipy + Typer + uv) aligns with the project's existing toolchain and Orlando's AI agent tooling context
- The discovery endpoint removal is not a blocker — the architecture already positions the LLM as the track source and Spotify as the write target

## Next Steps

- [ ] Register app at `developer.spotify.com`; set redirect URI to `http://127.0.0.1:8888/callback`
- [ ] Add `SPOTIFY_CLIENT_ID` to `.env.example` and document in README
- [ ] Implement `auth login` / `auth logout` commands using `SpotifyPKCE` with explicit `cache_path`
- [ ] Implement `playlist create` command: accept JSON track list → search URIs → POST `/me/playlists` → POST `/playlists/{id}/items`
- [ ] Add `Retry-After` handling for 429 responses
- [ ] Write integration tests against Spotify sandbox (using a test account in the 5-user cap)

## Sources

- [Spotify Web API Authorization Guide — PKCE](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow)
- [Spotify Web API — Playlist Endpoints](https://developer.spotify.com/documentation/web-api/reference/create-playlist)
- [spotipy Documentation](https://spotipy.readthedocs.io/en/latest/)
- [spotipy GitHub — CVE-2025-27154 fix](https://github.com/spotipy-dev/spotipy)
- `~/Documents/Library/10-Reference/Professional/Computing/Spotify-Web-API.md` — Full API reference (auth flows, endpoints, rate limits, gotchas)
- `~/Documents/Library/10-Reference/Professional/Computing/Spotify-CLI-Tooling.md` — Libraries, CLI architecture patterns, implementation blueprint

---

Last Updated: 2026-06-02
