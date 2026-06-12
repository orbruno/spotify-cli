import json
import time
import typer
from spotify_cli.core.spotify_client import (
    CACHE_PATH,
    get_auth_manager,
    get_cached_token,
    require_client_id,
)


def login(
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Print auth URL to stdout and accept redirect URL via stdin (headless/SSH).",
    )
) -> None:
    """
    Authenticate with Spotify via OAuth 2.0 PKCE.

    Usage: spotify-cli auth login [--no-browser]
    Example: spotify-cli auth login
    Example: spotify-cli auth login --no-browser
    """
    require_client_id()
    auth_manager = get_auth_manager(open_browser=not no_browser)
    auth_manager.get_access_token(as_dict=False)
    typer.echo(json.dumps({"status": "authenticated", "cache_path": str(CACHE_PATH)}))
    raise typer.Exit(code=0)


def status() -> None:
    """
    Print current token status as JSON.

    Reads the cache file directly via ``CacheFileHandler`` and does not require
    ``SPOTIFY_CLIENT_ID``; an absent or unreadable cache reports ``missing``.

    Usage: spotify-cli auth status
    Example: spotify-cli auth status
    """
    if not CACHE_PATH.exists():
        typer.echo(json.dumps({"status": "missing"}))
        raise typer.Exit(code=0)

    token_info = get_cached_token()

    if token_info is None:
        typer.echo(json.dumps({"status": "missing"}))
        raise typer.Exit(code=0)

    expires_in = int(token_info["expires_at"] - time.time())
    state = "valid" if expires_in > 0 else "expired"
    output: dict = {"status": state, "expires_in_seconds": expires_in}

    if state == "valid":
        output["scopes"] = token_info.get("scope", "").split()

    typer.echo(json.dumps(output))
    raise typer.Exit(code=0)


def logout() -> None:
    """
    Delete cached Spotify tokens.

    Usage: spotify-cli auth logout
    Example: spotify-cli auth logout
    """
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
        typer.echo(json.dumps({"status": "logged_out"}))
    else:
        typer.echo(json.dumps({"status": "no_session"}))
    raise typer.Exit(code=0)
