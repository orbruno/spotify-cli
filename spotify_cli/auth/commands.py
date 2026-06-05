import typer
from spotify_cli.core.spotify_client import require_client_id


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
    """
    require_client_id()
    raise NotImplementedError("Full login flow implemented in E1-S3")


def status() -> None:
    """
    Print current token status as JSON.

    Usage: spotify-cli auth status
    Example: spotify-cli auth status
    """
    raise NotImplementedError("Implemented in E1-S4")


def logout() -> None:
    """
    Delete cached Spotify tokens.

    Usage: spotify-cli auth logout
    Example: spotify-cli auth logout
    """
    raise NotImplementedError("Implemented in E1-S4")
