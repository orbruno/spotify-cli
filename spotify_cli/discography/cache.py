from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path.home() / ".config" / "spotify-cli" / "cache" / "discography"
TTL_SECONDS = 86400  # 24 hours


def cache_path(artist_id: str) -> Path:
    return CACHE_DIR / f"{artist_id}.json"


def is_valid(artist_id: str) -> bool:
    path = cache_path(artist_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data["cached_at"].replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
        return age_seconds < TTL_SECONDS
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def read(artist_id: str) -> list[dict]:
    path = cache_path(artist_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("tracks", [])
    except (json.JSONDecodeError, OSError):
        return []


def write(artist_id: str, artist_name: str, tracks: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "artist_id": artist_id,
        "artist_name": artist_name,
        "cached_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ttl_seconds": TTL_SECONDS,
        "tracks": tracks,
    }
    target = cache_path(artist_id)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)  # atomic on POSIX and Windows


def clear() -> None:
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            f.unlink(missing_ok=True)
