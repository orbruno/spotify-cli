# Track List Input Contract — JSON stdin for Agent Invocation

**Version**: 1.0
**Created**: 2026-06-03
**Author**: Orlando Bruno
**Status**: Accepted
**Area**: sys
**Related Documents**: [PRD](../01_PRD/prd.md), [ADR-002__sys__track-resolution-strategy.md](./ADR-002__sys__track-resolution-strategy.md), [Spotify API Research](../02_Research/01_Spotify-API-Playlist-Creation.md)

---

## Executive Summary

The `playlist add-tracks` command needs a single, consistent input contract that works for both an AI agent invoking the CLI as a subprocess and a human developer using it interactively. JSON array via stdin is chosen as the primary interface because it eliminates shell quoting complexity, handles arbitrarily large track lists, and maps directly to the structured output an LLM produces. Repeated `--uri` flags and `--file` are retained as convenience aliases resolving to the same internal parser.

---

## 1. Problem Statement

### Context

The CLI has two user types: a human developer running commands interactively, and an AI agent invoking the CLI as a subprocess. Both need a way to pass a list of tracks (Spotify URIs, or artist+track pairs for search-first fallback) to the `playlist add-tracks` command.

The input contract must satisfy:
- Agent invocability: the LLM can construct and pass the input without shell quoting complexity
- Scriptability: works reliably in non-TTY contexts (piped, no terminal)
- Human usability: a developer can also construct it without writing a JSON file by hand
- Structured enough to carry metadata (artist, track name, URI, optional notes)

### Desired Outcome

A single parsing path inside the CLI that accepts track lists from multiple surfaces (stdin, file, flags) and resolves them to an internal list before any API calls are made. The contract must be stable so agents built against it do not break when the CLI evolves.

---

## 2. Architecture Overview

```mermaid
flowchart TD
    A[Agent / Human Caller] -->|stdin JSON array| B[Input Parser]
    A -->|--uri flags| B
    A -->|--file path.json| B
    B --> C{URI present?}
    C -->|Yes| D[Direct add to batch]
    C -->|No: artist + track| E[Search-first fallback]
    E --> D
    D --> F[Batch into groups of 100]
    F --> G[POST /playlists/{id}/items]
    G --> H[Output JSON result]
```

The input parser is the single entry point for all track data. Regardless of input surface, all tracks converge to the same internal list before resolution and API batching.

---

## 3. Options Considered

### Option A: JSON stdin (chosen)

**Description**: Agent passes a JSON array to the CLI via stdin: `echo '[...]' | spotify-cli playlist add-tracks {id}`. Schema supports both URI-direct and search-first objects in the same array.

**Pros**:
- Idiomatic for agent/subprocess use — LLM serialises its structured output as JSON and pipes it directly
- No shell quoting issues — the JSON is a single stream, not individual arguments
- Handles arbitrarily large track lists (100+ tracks) without hitting shell argument limits
- Parseable with standard library (`json.loads(sys.stdin.read())`) — no extra dependencies
- Schema is extensible: add fields without breaking existing consumers

**Cons**:
- Not ergonomic for a human typing in a terminal
- CLI must detect whether stdin is a TTY to avoid hanging waiting for input when invoked interactively

### Option B: Repeated `--uri` flags

**Description**: `spotify-cli playlist add-tracks {id} --uri spotify:track:aaa --uri spotify:track:bbb`

**Pros**:
- Natural for small interactive invocations (1–5 tracks)
- Familiar CLI pattern

**Cons**:
- Shell argument limit becomes a problem at ~50+ URIs (OS-dependent, typically 2 MB)
- Verbose and awkward for agent construction — LLM must serialise each URI as a separate flag
- No metadata possible beyond the URI string

### Option C: Positional arguments

**Description**: `spotify-cli playlist add-tracks {id} uri1 uri2 uri3 ...`

**Pros**:
- Minimal syntax for human use

**Cons**:
- Even more awkward than repeated flags for agent construction
- No metadata possible (artist name, track name) — URIs only
- Superseded by Option A for all non-trivial use cases

### Option D: File path

**Description**: `spotify-cli playlist add-tracks {id} --file tracks.json`

**Pros**:
- Useful when the track list is pre-generated and saved to disk
- Human-readable source file

**Cons**:
- Forces the agent to write a temp file before invoking the CLI — adds an extra step
- Not suitable as the primary interface for in-memory agent output

---

## 4. Chosen Solution

**Decision**: Option A — JSON array via stdin as primary input contract, with Options B and D retained as convenience aliases.

**Rationale**:
- JSON stdin is the natural handoff between an LLM's structured output and the CLI process
- All input surfaces (stdin, `--file`, `--uri` flags) resolve to the same internal list, keeping the parsing path simple and testable
- `--uri` flags cover interactive single-track use without requiring JSON knowledge
- `--file` covers pre-generated lists on disk without requiring the caller to pipe
- The mutual-exclusion rule (only one input source at a time) prevents ambiguity

---

## 5. Implementation Specification

### Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Input parser | Detect input source (TTY check, flag presence), read and validate JSON or URI list | Python stdlib (`sys.stdin`, `json`, `re`) |
| Track resolver | Route each item: URI-direct → batch, no-URI → search fallback | Internal module, calls Spotify search API |
| Batch splitter | Chunk resolved URIs into groups of ≤100 | Pure function |
| Playlist writer | POST each batch to `/playlists/{id}/items` | Spotify Web API client |
| Result serialiser | Aggregate per-track status into output schema | Python dataclass → JSON |

### Key Interfaces

**Input schema**:

```json
[
  {
    "uri": "spotify:track:3tnXNkDnn8cpGE1x7QNBQV",
    "name": "Hurt",
    "artist": "Johnny Cash"
  },
  {
    "artist": "Townes Van Zandt",
    "track": "Pancho and Lefty"
  }
]
```

- `uri` present → add directly, no search needed
- `uri` absent, `artist` + `track` present → resolve via search-first fallback
- `name` and `artist` on URI objects are optional metadata for logging/confirmation output only

**Output schema**:

```json
{
  "playlist_id": "37i9dQZF1DX...",
  "tracks_added": 10,
  "tracks_failed": 0,
  "results": [
    {
      "input": { "uri": "spotify:track:xxx", "name": "Hurt", "artist": "Johnny Cash" },
      "status": "added"
    },
    {
      "input": { "artist": "Townes Van Zandt", "track": "Pancho and Lefty" },
      "status": "failed",
      "reason": "no match found"
    }
  ]
}
```

**Input detection order**:
1. `--uri` flags present → use flag list
2. `--file path` present → read file, parse as JSON array
3. stdin is not a TTY → read and parse stdin as JSON array
4. stdin is a TTY and no flags → print usage, exit 2

---

## 6. Performance & Cost

| Metric | Expected | Target |
|--------|----------|--------|
| Tracks per API call | 100 (Spotify limit) | ≤100 |
| Latency per batch | ~200–400 ms | <500 ms |
| Shell arg ceiling | N/A (stdin, no arg limit) | Unlimited |
| Memory for large lists | Linear in list size | Acceptable for ≤10k tracks |

---

## 7. Quality Assurance & Validation

### Success Metrics

- [ ] Agent can pipe a 200-track JSON array and all tracks are added (or failures reported) correctly
- [ ] `--uri` flag accepts 1–50 URIs without error
- [ ] `--file` reads a valid JSON file and processes it identically to stdin
- [ ] Mutual exclusion: providing `--uri` and piping stdin simultaneously exits 2
- [ ] Invalid URI format causes exit 3 with a clear error message
- [ ] `--dry-run` prints resolved batch payload as JSON and exits 0 without writing to playlist
- [ ] Interactive invocation (TTY, no flags) prints usage and exits 2

### Testing Strategy

- **Unit tests**: input parser (all four detection branches), batch splitter (boundary at 100), URI validator regex
- **Integration tests**: mock Spotify API, verify correct batch payloads sent for mixed URI/search input
- **E2E tests**: full subprocess invocation with piped JSON, assert output schema matches spec

---

## 8. Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| stdin hang in interactive mode | High — blocks terminal | Medium | TTY detection (`sys.stdin.isatty()`) before reading |
| Ambiguous multi-source input | Medium — undefined behaviour | Low | Mutual exclusion check at startup; exit 2 with clear message |
| Malformed JSON from agent | Medium — unhelpful error | Medium | Catch `json.JSONDecodeError`, print line/col, exit 3 |
| Spotify batch limit exceeded | High — API 400 error | Low | Enforce ≤100 per batch in splitter; covered by unit test |
| Agent builds against unstable schema | High — silent breakage | Low | Schema versioning note in output; breaking changes → new ADR |

---

## 9. Implementation Roadmap

### Phase 1: Core stdin path

- [ ] Implement TTY detection and input source resolution
- [ ] Implement JSON schema validation (required fields, URI format)
- [ ] Implement batch splitter (≤100)
- [ ] Wire to `POST /playlists/{id}/items`
- [ ] Emit output schema to stdout

### Phase 2: Convenience aliases

- [ ] Implement `--uri` flag (single or repeated)
- [ ] Implement `--file path` alias
- [ ] Enforce mutual exclusion across all three input sources

### Phase 3: Polish

- [ ] `--dry-run` flag (FR-12): print resolved batch payload, exit 0
- [ ] Search-first fallback integration (see ADR-002)
- [ ] E2E test suite covering agent subprocess invocation

---

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-03 | Adopt JSON stdin as primary input contract | Best fit for agent invocability and unlimited track list size |
| 2026-06-03 | Retain `--uri` flags as convenience | Human ergonomics for small interactive invocations |
| 2026-06-03 | `--file` as stdin alias, not primary | Avoids forcing temp-file creation in agent workflows |

---

## 11. Success Criteria

- [ ] `echo '[{"uri":"spotify:track:xxx"}]' | spotify-cli playlist add-tracks {id}` adds the track and prints valid output JSON
- [ ] A 200-track list is processed in ≤3 batches with correct per-track result reporting
- [ ] No regression on interactive (`--uri`) usage for human developers
- [ ] `--dry-run` is safe to run in CI without a live Spotify token

---

## 12. Related Documents

- [PRD — FR-06, FR-07, FR-12, NFR-05, NFR-09, NFR-14, NFR-15](../01_PRD/prd.md)
- [ADR-002 — Track Resolution Strategy](./ADR-002__sys__track-resolution-strategy.md)
- [Research — Spotify API Playlist Creation (batch add endpoint)](../02_Research/01_Spotify-API-Playlist-Creation.md)

---

**Last Updated**: 2026-06-03 by Orlando Bruno
