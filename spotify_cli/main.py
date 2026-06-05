import typer
from spotify_cli.auth import commands as auth_commands

__version__ = "0.1.0"

app = typer.Typer(
    help="Spotify CLI — manage your Spotify account from the terminal.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
auth_app = typer.Typer(
    help="Authentication commands.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
# context_settings propagates to all subcommands registered on auth_app
# No per-command override needed unless a command uses a custom Context
app.add_typer(auth_app, name="auth")

auth_app.command("login")(auth_commands.login)
auth_app.command("status")(auth_commands.status)
auth_app.command("logout")(auth_commands.logout)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"spotify-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


if __name__ == "__main__":
    app()
