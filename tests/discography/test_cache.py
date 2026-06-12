import json
from datetime import datetime, timedelta, timezone

from spotify_cli.discography import cache as cache_mod

TRACKS = [
    {
        "uri": "spotify:track:abc",
        "name": "Hurt",
        "artist": "Johnny Cash",
        "album": "American IV",
        "release_date": "2002-11-05",
        "track_number": 1,
        "duration_ms": 220000,
        "explicit": False,
    }
]


def test_is_valid_returns_false_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    assert cache_mod.is_valid("missing") is False


def test_write_then_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    cache_mod.write("abc", "Johnny Cash", TRACKS)
    assert cache_mod.is_valid("abc") is True
    assert cache_mod.read("abc") == TRACKS


def test_is_valid_returns_false_when_ttl_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    expired_at = (
        (datetime.now(timezone.utc) - timedelta(seconds=86401))
        .isoformat()
        .replace("+00:00", "Z")
    )
    payload = {
        "artist_id": "abc",
        "artist_name": "Johnny Cash",
        "cached_at": expired_at,
        "ttl_seconds": 86400,
        "tracks": [],
    }
    (tmp_path / "abc.json").write_text(json.dumps(payload), encoding="utf-8")
    assert cache_mod.is_valid("abc") is False


def test_corrupt_json_treated_as_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    (tmp_path / "abc.json").write_text("{not valid json", encoding="utf-8")
    assert cache_mod.is_valid("abc") is False
    assert cache_mod.read("abc") == []


def test_missing_cached_at_key_treated_as_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    (tmp_path / "abc.json").write_text(json.dumps({"tracks": []}), encoding="utf-8")
    assert cache_mod.is_valid("abc") is False


def test_write_is_atomic_no_tmp_file_left(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    cache_mod.write("abc", "Johnny Cash", TRACKS)
    assert (tmp_path / "abc.json").exists() is True
    assert (tmp_path / "abc.tmp").exists() is False


def test_clear_removes_all_json_files(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    cache_mod.write("abc", "Johnny Cash", TRACKS)
    cache_mod.write("def", "Nine Inch Nails", TRACKS)
    cache_mod.clear()
    assert list(tmp_path.glob("*.json")) == []


def test_read_returns_empty_list_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    assert cache_mod.read("missing") == []
