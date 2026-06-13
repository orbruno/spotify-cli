from inspect import isgeneratorfunction
from unittest.mock import MagicMock, patch

import pytest
from spotipy.exceptions import SpotifyException

from spotify_cli.discography.fetcher import (
    ArtistNotFoundError,
    _call_with_retry,
    apply_year_filter,
    fetch_albums,
    iter_tracks,
    resolve_artist,
)


def _album(name="Album", release_date="2002-11-05", album_id="alb1"):
    return {"id": album_id, "name": name, "release_date": release_date}


def _track(uri="spotify:track:abc", name="Hurt"):
    return {"uri": uri, "name": name, "track_number": 1, "duration_ms": 220000, "explicit": False}


def _429_exception(headers=None):
    return SpotifyException(
        429,
        -1,
        "rate limited",
        headers={"Retry-After": "2"} if headers is None else headers,
    )


def test_resolve_artist_returns_id_and_name():
    sp = MagicMock()
    sp.search.return_value = {
        "artists": {"items": [{"id": "6kAC", "name": "Johnny Cash", "popularity": 80}]}
    }

    result = resolve_artist(sp, "Johnny Cash")

    assert result == {"id": "6kAC", "name": "Johnny Cash"}
    sp.search.assert_called_once_with(q="Johnny Cash", type="artist", limit=1)


def test_resolve_artist_raises_when_not_found():
    sp = MagicMock()
    sp.search.return_value = {"artists": {"items": []}}

    with pytest.raises(ArtistNotFoundError, match="No Spotify artist matched"):
        resolve_artist(sp, "Nonexistent Artist XYZ")


def test_fetch_albums_paginates_when_page_all():
    sp = MagicMock()
    page1 = {"items": [_album(album_id="alb1")], "next": "https://api/next"}
    page2 = {"items": [_album(album_id="alb2")], "next": None}
    sp.artist_albums.return_value = page1
    sp.next.return_value = page2

    albums = fetch_albums(sp, "artist1", page_all=True)

    assert [a["id"] for a in albums] == ["alb1", "alb2"]
    sp.next.assert_called_once_with(page1)


def test_fetch_albums_default_returns_first_page_only():
    sp = MagicMock()
    sp.artist_albums.return_value = {
        "items": [_album(album_id="alb1")],
        "next": "https://api/next",
    }

    albums = fetch_albums(sp, "artist1")

    assert len(albums) == 1
    sp.next.assert_not_called()


def test_fetch_albums_maps_all_album_type():
    sp = MagicMock()
    sp.artist_albums.return_value = {"items": [], "next": None}

    fetch_albums(sp, "artist1", album_type="all")

    kwargs = sp.artist_albums.call_args.kwargs
    assert kwargs["album_type"] == "album,single,compilation,appears_on"


def test_fetch_albums_passes_single_album_type_through():
    sp = MagicMock()
    sp.artist_albums.return_value = {"items": [], "next": None}

    fetch_albums(sp, "artist1", album_type="single")

    kwargs = sp.artist_albums.call_args.kwargs
    assert kwargs["album_type"] == "single"


def test_apply_year_filter_excludes_out_of_range():
    albums = [
        _album(release_date="1994", album_id="a"),
        _album(release_date="2002-11", album_id="b"),
        _album(release_date="2010-05-01", album_id="c"),
    ]

    result = apply_year_filter(albums, from_year=2000, to_year=2005)

    assert [a["release_date"] for a in result] == ["2002-11"]


def test_apply_year_filter_no_bounds_returns_all():
    albums = [
        _album(release_date="1994", album_id="a"),
        _album(release_date="2010-05-01", album_id="c"),
    ]

    result = apply_year_filter(albums)

    assert result == albums


def test_iter_tracks_is_generator_function():
    assert isgeneratorfunction(iter_tracks)


def test_iter_tracks_yields_flat_track_dicts():
    sp = MagicMock()
    album = _album(name="American IV", release_date="2002-11-05")
    sp.album_tracks.return_value = {"items": [_track()], "next": None}

    tracks = list(iter_tracks(sp, [album], "Johnny Cash"))

    assert len(tracks) == 1
    assert tracks[0] == {
        "uri": "spotify:track:abc",
        "name": "Hurt",
        "artist": "Johnny Cash",
        "album": "American IV",
        "release_date": "2002-11-05",
        "track_number": 1,
        "duration_ms": 220000,
        "explicit": False,
    }


def test_iter_tracks_paginates_track_pages():
    sp = MagicMock()
    album = _album()
    page1 = {"items": [_track(uri="spotify:track:one", name="One")], "next": "https://api/next"}
    page2 = {"items": [_track(uri="spotify:track:two", name="Two")], "next": None}
    sp.album_tracks.return_value = page1
    sp.next.return_value = page2

    tracks = list(iter_tracks(sp, [album], "Johnny Cash"))

    assert [t["uri"] for t in tracks] == ["spotify:track:one", "spotify:track:two"]


def test_429_sleeps_and_retries_then_succeeds():
    func = MagicMock(side_effect=[_429_exception(), {"items": []}])

    with patch("spotify_cli.discography.fetcher.time.sleep") as mock_sleep:
        result = _call_with_retry(func)

    assert result == {"items": []}
    mock_sleep.assert_called_once_with(2)
    assert func.call_count == 2


def test_429_reraised_after_max_retries():
    func = MagicMock(side_effect=_429_exception())

    with patch("spotify_cli.discography.fetcher.time.sleep") as mock_sleep:
        with pytest.raises(SpotifyException):
            _call_with_retry(func)

    assert func.call_count == 4  # 1 initial + 3 retries
    assert mock_sleep.call_count == 3


def test_429_defaults_to_one_second_without_header():
    func = MagicMock(side_effect=[_429_exception(headers={}), "ok"])

    with patch("spotify_cli.discography.fetcher.time.sleep") as mock_sleep:
        result = _call_with_retry(func)

    assert result == "ok"
    mock_sleep.assert_called_once_with(1)


def test_non_429_spotify_exception_raises_immediately():
    func = MagicMock(side_effect=SpotifyException(404, -1, "not found", headers={}))

    with patch("spotify_cli.discography.fetcher.time.sleep") as mock_sleep:
        with pytest.raises(SpotifyException):
            _call_with_retry(func)

    assert func.call_count == 1
    mock_sleep.assert_not_called()
