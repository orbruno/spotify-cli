# Story: Playlist Tests

**Epic**: [E3 - Playlist Creation](../Epics/E3_Playlist-Creation.md)
**Story ID**: E3-S5
**Story Points**: 3
**Priority**: Medium
**Status**: To Do

## User Story

As a **developer**,
I want a **complete test suite for the playlist module covering all input modes, batch chunking, resolver paths, and error exits**,
So that **agent-facing behaviour is locked down before release and regressions are caught automatically**.

## Description

Write the full test suite for the four playlist modules across four test files. All tests use a mocked Spotipy client — no live API calls. The suite maps directly to the 12 test cases defined in SPEC-003 §2.6 (TC-01 through TC-12), plus the two auth/resource-not-found cases (TC-13, TC-14). Coverage must reach ≥80% across all four modules.

Note: individual stories (E3-S1 through E3-S4) each include their own unit tests as part of their Definition of Done. This story consolidates the full suite, ensures nothing is missed, and verifies the combined coverage threshold is met.

## Acceptance Criteria

- [ ] `uv run pytest tests/playlist/test_input_parser.py` passes — all input modes, URI validation, path traversal, mutual exclusion
- [ ] `uv run pytest tests/playlist/test_batch.py` passes — chunking, 429 retry, partial failure
- [ ] `uv run pytest tests/playlist/test_resolver.py` passes — URI passthrough, search hit, search miss
- [ ] `uv run pytest tests/playlist/test_commands.py` passes — TC-01 through TC-12 (plus TC-13, TC-14)
- [ ] All 12 named test cases (TC-01 through TC-12) are implemented and passing
- [ ] Spotipy is mocked in all tests — no live API calls made during `uv run pytest`
- [ ] `uv run pytest tests/playlist/ --cov=spotify_cli/playlist --cov-fail-under=80` passes

## Technical Notes

### Implementation Approach

Use `unittest.mock.MagicMock` for the Spotipy client. Use `typer.testing.CliRunner(mix_stderr=False)` for command integration tests to capture stdout and stderr separately. Use `monkeypatch.setenv` for auth env vars. Use `tmp_path` fixture for `--file` tests.

Shared mock fixture in `test_commands.py`:

```python
@pytest.fixture
def mock_sp():
    sp = MagicMock()
    sp.current_user.return_value = {"id": "test_user"}
    sp.user_playlist_create.return_value = {
        "id": "playlist123",
        "name": "Test",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist123"},
        "public": False,
    }
    sp.playlist_add_items.return_value = {}
    sp.search.return_value = {"tracks": {"items": [{"uri": "spotify:track:resolved"}]}}
    return sp
```

### Test Case Coverage Map

| TC | File | Test function |
|----|------|---------------|
| TC-01 | test_commands.py | `test_create` |
| TC-02 | test_commands.py | `test_add_tracks_stdin` |
| TC-03 | test_commands.py | `test_add_tracks_dry_run` |
| TC-04 | test_resolver.py | `test_search_hit` |
| TC-05 | test_resolver.py | `test_search_miss` |
| TC-06 | test_input_parser.py | `test_invalid_uri_format` |
| TC-07 | test_input_parser.py | `test_ambiguous_input_sources` |
| TC-08 | test_input_parser.py | `test_tty_no_flags` |
| TC-09 | test_batch.py | `test_150_tracks_two_batches` |
| TC-10 | test_commands.py | `test_create_and_add` |
| TC-11 | test_commands.py | `test_add_tracks_file` |
| TC-12 | test_input_parser.py | `test_path_traversal` |
| TC-13 | test_commands.py | `test_not_authenticated` |
| TC-14 | test_commands.py | `test_playlist_not_found` |

### Files/Components Affected

- `tests/playlist/test_input_parser.py` — all input modes, error paths
- `tests/playlist/test_batch.py` — chunking, partial failure, 429 retry
- `tests/playlist/test_resolver.py` — URI passthrough, search hit, search miss
- `tests/playlist/test_commands.py` — TC-01 through TC-14 via Typer CliRunner

### External Dependencies

- `pytest` — test runner
- `pytest-cov` — coverage reporting
- `typer[testing]` — `CliRunner`
- `unittest.mock` (stdlib) — `MagicMock`, `patch`

## Definition of Done

- [ ] All four test files implemented
- [ ] All 14 test cases (TC-01 through TC-14) passing
- [ ] Coverage ≥80% across all four `playlist/` modules
- [ ] No live Spotipy calls (verified via `assert mock_sp.search.call_count`)
- [ ] `uv run pytest tests/playlist/ -v` exits 0
- [ ] Self-reviewed
- [ ] No known bugs or issues

## Dependencies

**Depends On**:
- E3-S1 (Input Parser): `test_input_parser.py` tests this module
- E3-S2 (Batch Module): `test_batch.py` tests this module
- E3-S3 (Search Resolver): `test_resolver.py` tests this module
- E3-S4 (Playlist Commands): `test_commands.py` tests the integrated command app

**Blocks**:
- Nothing — this is the final story in E3.

## Related Stories

- E3-S1: Input Parser — primary target of `test_input_parser.py`
- E3-S2: Batch Module — primary target of `test_batch.py`
- E3-S3: Search Resolver — primary target of `test_resolver.py`
- E3-S4: Playlist Commands — primary target of `test_commands.py`

## Notes

- SPEC-003 §3.5 (Phase 5) contains full implementation tasks (T-25 through T-30) and the `test_commands.py` scaffold.
- The full `test_commands.py` scaffold (including all fixture definitions) is provided in SPEC-003 §3.5 — use it as the starting point.
- Run `uv run pytest tests/playlist/ --cov=spotify_cli/playlist --cov-report=term-missing` for a line-by-line coverage report during development.
- Individual stories (E3-S1 through E3-S4) each write their own tests as part of their DoD; this story owns the final coverage gate and the consolidated TC mapping.

---

**Created**: 2026-06-04
**Status**: Ready for Sprint Planning
