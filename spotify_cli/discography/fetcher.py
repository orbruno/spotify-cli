from __future__ import annotations

import time
from typing import Any, Callable, Generator

import spotipy
from spotipy.exceptions import SpotifyException

MAX_RETRIES = 3


class ArtistNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No Spotify artist matched '{name}'")


def _call_with_retry(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call a spotipy API method, retrying on HTTP 429 up to MAX_RETRIES times.

    Sleeps for the Retry-After header value (default 1s) between attempts.
    Non-429 errors and the final 429 are re-raised.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except SpotifyException as exc:
            if exc.http_status != 429 or attempt == MAX_RETRIES:
                raise
            headers = getattr(exc, "headers", None) or {}
            time.sleep(int(headers.get("Retry-After", 1)))


def resolve_artist(sp: spotipy.Spotify, name: str) -> dict:
    results = sp.search(q=name, type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])
    if not items:
        raise ArtistNotFoundError(name)
    artist = items[0]
    return {"id": artist["id"], "name": artist["name"]}


def fetch_albums(
    sp: spotipy.Spotify,
    artist_id: str,
    album_type: str = "album",
    page_all: bool = False,
) -> list[dict]:
    api_album_type = (
        "album,single,compilation,appears_on" if album_type == "all" else album_type
    )
    albums: list[dict] = []
    response = _call_with_retry(
        sp.artist_albums, artist_id, album_type=api_album_type, limit=50
    )
    while response:
        albums.extend(response["items"])
        response = sp.next(response) if (page_all and response.get("next")) else None
    return albums


def apply_year_filter(
    albums: list[dict],
    from_year: int | None = None,
    to_year: int | None = None,
) -> list[dict]:
    def year_of(album: dict) -> int:
        # release_date can be "YYYY", "YYYY-MM", or "YYYY-MM-DD"
        return int(album["release_date"][:4])

    return [
        a
        for a in albums
        if (from_year is None or year_of(a) >= from_year)
        and (to_year is None or year_of(a) <= to_year)
    ]


def iter_tracks(
    sp: spotipy.Spotify,
    albums: list[dict],
    artist_name: str,
) -> Generator[dict, None, None]:
    for album in albums:
        response = _call_with_retry(sp.album_tracks, album["id"], limit=50)
        while response:
            for track in response["items"]:
                yield {
                    "uri": track["uri"],
                    "name": track["name"],
                    "artist": artist_name,
                    "album": album["name"],
                    "release_date": album["release_date"],
                    "track_number": track["track_number"],
                    "duration_ms": track["duration_ms"],
                    "explicit": track["explicit"],
                }
            response = sp.next(response) if response.get("next") else None
