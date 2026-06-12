# Sprint-02 Manual Verification Pending

The Sprint-02 automated test suite (14 tests, 100% coverage of `auth/` and `core/`) verifies:
- Command argument plumbing and JSON output shapes
- Exit codes for every documented state
- `login()`'s contract with Spotipy (`get_access_token(as_dict=False)`)
- `status()` independence from `SPOTIFY_CLIENT_ID` when a cache exists
- Expired-token branch, missing-cache branch, cached-token-`None` edge case
- `logout()` idempotency without a cache

The following acceptance criteria require a live OAuth flow with a real `SPOTIFY_CLIENT_ID` and **cannot be verified by automated tests**. They must be checked manually after a Spotify developer-dashboard entry registers `http://127.0.0.1:9090/callback` for the chosen client.

---

## E1-S3 — Auth Login (live OAuth)

| Item | How to verify | Pass criteria | Status |
|------|---------------|---------------|--------|
| First run opens browser and captures redirect at `http://127.0.0.1:9090/callback` | `export SPOTIFY_CLIENT_ID=<real-id> && uv run spotify-cli auth login` | Default browser launches Spotify authorize page; after consent, terminal prints `{"status": "authenticated", "cache_path": "..."}` and exits 0 | ⏳ Pending |
| Token written to `~/.config/spotify-cli/.cache` with permissions `600` | After successful login: `stat -f "%A" ~/.config/spotify-cli/.cache` | Output: `600` | ⏳ Pending |
| Subsequent runs within TTL do not open browser (silent refresh via Spotipy) | Run `uv run spotify-cli auth login` again within ~1h | Second run exits 0 with same JSON, no browser launch | ⏳ Pending |
| `--no-browser` prints auth URL to stdout and accepts redirect URL via stdin (headless/SSH) | First clear cache: `uv run spotify-cli auth logout`. Then: `uv run spotify-cli auth login --no-browser` | Terminal prints the Spotify authorize URL, waits for paste of the post-redirect URL on stdin; on paste, exits 0 with authenticated JSON | ⏳ Pending |

## E1-S4 — Status & Logout (live cache)

| Item | How to verify | Pass criteria | Status |
|------|---------------|---------------|--------|
| `auth status` with a real cached valid token returns `status=valid` + populated `scopes` | After live login: `uv run spotify-cli auth status` | JSON has `status: "valid"`, positive `expires_in_seconds`, `scopes` array containing `playlist-modify-public`, `playlist-modify-private`, `user-read-private` | ⏳ Pending |
| `auth status` correctly reports `expired` once TTL passes (no live refresh by `status`) | Wait > `expires_in_seconds`, then run `auth status` without re-logging-in | JSON has `status: "expired"` and negative `expires_in_seconds` | ⏳ Pending |
| `auth logout` deletes the real cache file from disk | After live login: `uv run spotify-cli auth logout` then `ls -la ~/.config/spotify-cli/` | `.cache` is gone; JSON is `{"status": "logged_out"}` | ⏳ Pending |

---

## Out of Scope for This Sprint

- `~/.config/spotify-cli/.cache` permissions are enforced by Spotipy (`>=2.25.1`). If the manual check fails, the fix is in Spotipy's `CacheFileHandler`, not this codebase.
- True silent-refresh behavior is owned by Spotipy. Our contract with Spotipy is `get_access_token(as_dict=False)` (TC-08 reworked).

---

**Owner**: Orlando Bruno
**Prerequisite**: Spotify Developer Dashboard entry with redirect URI `http://127.0.0.1:9090/callback` registered for the client ID used.
