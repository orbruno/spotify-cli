import os
import pathlib
import typer
import spotipy
from spotipy.oauth2 import SpotifyPKCE

CACHE_PATH = pathlib.Path.home() / ".config" / "spotify-cli" / ".cache"
SCOPES = "playlist-modify-public playlist-modify-private user-read-private"
REDIRECT_URI = "http://127.0.0.1:9090/callback"


def require_client_id() -> None:
    """Guard: exits with code 2 and structured JSON on stderr if SPOTIFY_CLIENT_ID is not set."""
    if not os.environ.get("SPOTIFY_CLIENT_ID"):
        typer.echo(
            '{"error": "SPOTIFY_CLIENT_ID not set", '
            '"reason": "Required env var missing", '
            '"suggestion": "export SPOTIFY_CLIENT_ID=your_client_id", '
            '"help": "spotify-cli auth --help"}',
            err=True,
        )
        raise typer.Exit(code=2)


def get_auth_manager(open_browser: bool = True) -> SpotifyPKCE:
    """
    Construct and return a SpotifyPKCE instance with CacheFileHandler.

    Creates the cache directory (~/.config/spotify-cli/) if it does not exist.
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SpotifyPKCE(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_handler=spotipy.cache_handler.CacheFileHandler(
            cache_path=str(CACHE_PATH)
        ),
        open_browser=open_browser,
    )


def get_cached_token() -> dict | None:
    """
    Read the cached token from disk without instantiating SpotifyPKCE.

    Returns the cached token dict (with ``access_token``, ``expires_at``,
    ``scope``, etc.) or ``None`` if the cache is empty or malformed.
    Does NOT require ``SPOTIFY_CLIENT_ID`` — pure file read.
    """
    return spotipy.cache_handler.CacheFileHandler(
        cache_path=str(CACHE_PATH)
    ).get_cached_token()


class NotAuthenticatedError(Exception):
    """Raised when no cached Spotify token is available."""


def get_spotify_client() -> spotipy.Spotify:
    """
    Return an authenticated spotipy.Spotify instance.

    Raises NotAuthenticatedError if no cached token exists. Token refresh is
    delegated to the SpotifyPKCE auth manager. Command-layer callers must run
    require_client_id() first — this factory assumes SPOTIFY_CLIENT_ID is set.
    """
    if get_cached_token() is None:
        raise NotAuthenticatedError(
            "Not authenticated. Run 'spotify-cli auth login' first."
        )
    return spotipy.Spotify(auth_manager=get_auth_manager())
