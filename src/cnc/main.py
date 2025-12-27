from __future__ import annotations

import typer
import click
from typer.main import get_command
from rich import print

from cnc.client import CampusNetClient, NeedUnauthed, StateError, AlreadyOffline, AlreadyOnline
from cnc.keep_alive import KeepAliveMode, keep_alive
from cnc.login import LoginError
from cnc.logout import LogoutError

app = typer.Typer(
    help="Campus network control (cnc)",
    context_settings={"help_option_names": ["-h", "--help"]},
)

client = CampusNetClient()


@app.command()
def login(
    user_id: str = typer.Option(..., "--user-id", envvar="CNC_USER_ID"),
    password: str = typer.Option(
        ..., "--password", envvar="CNC_PASSWORD", hide_input=True
    ),
    service: str = typer.Option(
        ...,
        "--service",
        envvar="CNC_SERVICE",
        help="Service name: 电信 or 移动",
    ),
):
    """
    Login to campus network.

    Args:
        user_id: User identifier for the portal.
        password: User password.
        service: Service name to authenticate against.

    Returns:
        None.
    """
    try:
        client.login(user_id, password, service)
        print("[green]Login successful[/green]")
    except AlreadyOnline as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    except AlreadyOffline as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    except LoginError as e:
        typer.secho(f"Login failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except NeedUnauthed as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        raise typer.Exit(2)


@app.command()
def logout(
):
    """
    Logout from campus network.

    Returns:
        None.
    """
    try:
        client.logout()
        print("[green]Logged out successfully[/green]")
    except AlreadyOffline as e:
        typer.secho(str(e), fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    except (StateError, LogoutError) as e:
        typer.secho(f"Logout failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def status():
    """
    Show current network/authentication status.

    Returns:
        None.
    """
    st = client.status()
    print(f"Status: {st.value}")


@app.command("keep-alive")
def keep_alive_cmd(
    polling: bool = typer.Option(
        False,
        "--polling",
        help="Keep alive via polling (default if no mode flag is set)",
    ),
    relogin: bool = typer.Option(
        False,
        "--relogin",
        help="Keep alive by daily relogin",
    ),
    interval_seconds: int = typer.Option(
        300,
        "--interval-seconds",
        help="Polling interval in seconds",
    ),
    user_id: str | None = typer.Option(
        None,
        "--user-id",
        envvar="CNC_USER_ID",
        help="User ID for relogin mode",
    ),
    password: str | None = typer.Option(
        None,
        "--password",
        envvar="CNC_PASSWORD",
        hide_input=True,
        help="Password for relogin mode",
    ),
    service: str | None = typer.Option(
        None,
        "--service",
        envvar="CNC_SERVICE",
        help="Service name for relogin mode: 电信 or 移动",
    ),
    run_at: str = typer.Option(
        "05:00",
        "--run-at",
        help="Daily relogin time (HH:MM, 24h)",
    ),
):
    """
    Keep the connection alive by polling or scheduled relogin.

    Args:
        polling: Use polling mode.
        relogin: Use daily relogin mode.
        interval_seconds: Polling interval in seconds.
        user_id: User identifier for relogin mode.
        password: User password for relogin mode.
        service: Service name for relogin mode.
        run_at: Daily relogin time (HH:MM, 24h).

    Returns:
        None.
    """
    if polling and relogin:
        typer.secho("Choose only one mode: --polling or --relogin", fg=typer.colors.RED)
        raise typer.Exit(2)

    mode = KeepAliveMode.relogin if relogin else KeepAliveMode.polling
    if mode == KeepAliveMode.relogin and not all([user_id, password, service]):
        typer.secho(
            "relogin mode requires --user-id, --password, and --service",
            fg=typer.colors.RED,
        )
        raise typer.Exit(2)

    try:
        keep_alive(
            mode,
            test_func=client.status,
            interval_seconds=interval_seconds,
            user_id=user_id,
            password=password,
            service=service,
            run_at=run_at,
        )
    except Exception as e:
        typer.secho(f"Keep-alive failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


def main():
    """Entrypoint for the cnc CLI.

    Returns:
        None.
    """
    app()


@app.command()
def help(command: str | None = typer.Argument(None)):
    """
    Show help for cnc or a specific subcommand.

    Args:
        command: Optional subcommand name.

    Returns:
        None.
    """
    root = get_command(app)
    if command:
        sub = root.commands.get(command)
        if not sub:
            typer.secho(f"Unknown command: {command}", fg=typer.colors.RED)
            raise typer.Exit(2)
        ctx = click.Context(sub, info_name=f"cnc {command}")
        typer.echo(sub.get_help(ctx))
        return

    ctx = click.Context(root, info_name="cnc")
    typer.echo(root.get_help(ctx))


if __name__ == "__main__":
    main()
