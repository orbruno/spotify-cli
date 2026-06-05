# Story: Input Parser

**Epic**: [E3 - Playlist Creation](../Epics/E3_Playlist-Creation.md)
**Story ID**: E3-S1
**Story Points**: 3
**Priority**: High
**Status**: To Do

## User Story

As an **AI agent**,
I want to **pipe a JSON array of tracks to the CLI via stdin**,
So that **I can pass track lists without shell quoting complexity or argument length limits**.

## Description

Implement `spotify_cli/playlist/input_parser.py` — the entry point for all track list ingestion. The module detects which of the three mutually exclusive input modes is active (JSON stdin, `--uri` flags, or `--file`), enforces that only one is used per invocation, validates URI format against the Spotify pattern, rejects path traversal in `--file` arguments, and returns a normalized list of track dicts for downstream processing.

Mutual exclusivity is intentionally enforced here rather than in Typer, so the validation logic is fully testable in isolation from the CLI layer. This module has no Spotify API calls — it only reads and validates.

## Acceptance Criteria

- [ ] Valid JSON stdin produces a normalised track list
- [ ] `--uri` flags produce the same normalised list as equivalent stdin input
- [ ] `--file path.json` reads the file and produces a normalised list
- [ ] Multiple input sources provided simultaneously exits 2 with structured JSON error on stderr
- [ ] Stdin is TTY with no `--uri`/`--file` provided exits 2 with structured JSON error on stderr
- [ ] Any URI not matching `spotify:track:[a-zA-Z0-9]+` exits 3 with structured JSON error on stderr
- [ ] `--file` path containing `..` exits 3 with structured JSON error on stderr

## Technical Notes

### Implementation Approach

All inputs are normalised to a `list[dict]`, where each dict may contain any combination of `uri`, `name`, `artist`, and `track` keys. The `--uri` mode wraps each raw URI string as `{"uri": uri}`. After normalisation, `_validate_uris()` scans every item with a `uri` key and raises `InputError(code=3)` on the first mismatch.

Input source counting logic: sum `bool(uris)`, `file is not None`, and `not stdin_stream.isatty()`. If the count exceeds 1, raise `InputError(code=2)`. If the count is 0, raise `InputError(code=2)` with `message="no input"`.

### Code Examples (if helpful)

```python
URI_PATTERN = re.compile(r"^spotify:track:[a-zA-Z0-9]+$")

@dataclass
class InputError(Exception):
    message: str
    code: int
    reason: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "reason": self.reason,
            "suggestion": self.suggestion,
            "help": "spotify-cli playlist --help",
        }

def parse_track_input(
    uris: Optional[list[str]],
    file: Optional[Path],
    stdin_stream=None,
) -> list[dict]:
    ...
```

Full skeleton available in SPEC-003 §3.1.

### Files/Components Affected

- `spotify_cli/playlist/__init__.py` — create package
- `spotify_cli/playlist/input_parser.py` — implement
- `tests/playlist/__init__.py` — create test package
- `tests/playlist/test_input_parser.py` — unit tests

### External Dependencies

- `json` (stdlib)
- `re` (stdlib)
- `sys` (stdlib)
- `pathlib.Path` (stdlib)
- `dataclasses` (stdlib)

## Definition of Done

- [ ] Code implemented and follows conventions
- [ ] All acceptance criteria met
- [ ] Tests written and passing (`uv run pytest tests/playlist/test_input_parser.py`)
- [ ] Self-reviewed
- [ ] No Spotify API calls in this module (pure parsing)
- [ ] Integrated with main codebase (imported by `commands.py`)
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- None — this is the first module in the playlist stack.

**Blocks**:
- E3-S4 (Playlist Commands): `commands.py` imports `parse_track_input`

## Related Stories

- E3-S2: Batch Module — consumes normalised track list produced here
- E3-S3: Search Resolver — consumes normalised track list produced here
- E3-S4: Playlist Commands — calls `parse_track_input()` in all write commands
- E3-S5: Playlist Tests — `test_input_parser.py` covers TC-06, TC-07, TC-08, TC-12

## Notes

- SPEC-003 §3.1 (Phase 1) contains the full implementation tasks (T-01 through T-09) and the complete code skeleton.
- Test cases that map to this story: TC-06 (invalid URI), TC-07 (ambiguous source), TC-08 (TTY no flags), TC-12 (path traversal).
- The `stdin_stream` parameter defaults to `sys.stdin` but is injectable for testing without TTY concerns.

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
