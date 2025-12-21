#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import typer
import yaml

from cnc.login import login, LoginError
from cnc.logout import logout, LogoutError
from cnc.test import test
from cnc.keep_logged_in import keep_logged_in_v1, keep_logged_in_v2

app = typer.Typer(add_completion=False)


def _xdg_config_home() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return Path(xdg).expanduser() if xdg else (Path.home() / ".config")


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file must be a mapping/dict: {path}")
    return data


def load_config(
    userId: Optional[str],
    password: Optional[str],
    service: Optional[str],
    portalUrl: Optional[str],
) -> dict:
    """
    Priority:
      1) CLI args (if provided)
      2) ./config.yaml
      3) $XDG_CONFIG_HOME/cnc/config.yaml (or ~/.config/cnc/config.yaml)
    """
    cfg: dict = {}

    # 2) current dir
    cwd_cfg = Path.cwd() / "config.yaml"
    if cwd_cfg.exists():
        cfg.update(_load_yaml(cwd_cfg))

    # 3) XDG
    xdg_cfg = _xdg_config_home() / "cnc" / "config.yaml"
    if xdg_cfg.exists():
        cfg.update(_load_yaml(xdg_cfg))

    # 1) CLI override
    if userId is not None:
        cfg["userId"] = userId
    if password is not None:
        cfg["password"] = password
    if service is not None:
        cfg["service"] = service
    if portalUrl is not None:
        cfg["portalUrl"] = portalUrl

    return cfg


def require_fields(cfg: dict, fields: list[str]) -> None:
    missing = [k for k in fields if not cfg.get(k)]
    if missing:
        raise typer.Exit(code=2)  # 先抛，再在调用处给出更友好提示


def _print_missing(cfg: dict, fields: list[str]) -> None:
    missing = [k for k in fields if not cfg.get(k)]
    if missing:
        typer.secho(
            f"❌ Missing required config fields: {', '.join(missing)}",
            fg=typer.colors.RED,
            err=True,
        )
        typer.echo("   Provide them via CLI or config.yaml.", err=True)


# ---- Commands ----


@app.command()
def run(
    userId: Optional[str] = typer.Option(
        None, "--userId", help="Portal account userId"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", help="Portal account password"
    ),
    service: Optional[str] = typer.Option(
        None, "--service", help="Service name, e.g. 'internet'"
    ),
    portalUrl: Optional[str] = typer.Option(
        None, "--portalUrl", help="Portal host/ip, e.g. 10.254.241.19"
    ),
):
    """
    Default flow: test -> login if offline -> optional keep-alive interaction.
    """
    try:
        cfg = load_config(userId, password, service, portalUrl)
    except Exception as e:
        typer.secho(f"❌ Failed to read config: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    result = test()

    if result == 0:
        typer.echo("用户已离线！即将执行自动登录脚本...")
        time.sleep(2)

        _print_missing(cfg, ["userId", "password", "service", "portalUrl"])
        try:
            require_fields(cfg, ["userId", "password", "service", "portalUrl"])
        except typer.Exit:
            raise

        try:
            login(cfg["userId"], cfg["password"], cfg["service"], cfg["portalUrl"])
            typer.secho("✔️ Login successfully!", fg=typer.colors.GREEN)
        except LoginError as e:
            typer.secho(f"❌ Failed to login: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    elif result == 1:
        typer.echo("用户在线！")
    else:
        typer.echo("请您检查是否正处于学校范围，或者是否已经接入校园网...")
        typer.echo(str(result))
        raise typer.Exit(code=0)

    # Keep online interaction
    typer.echo("是否需要保持在线?(yes/no)")
    while True:
        choice = input().strip().lower()

        if choice in ("yes", "y"):
            typer.echo("请选择保持登入的模式...(1/2)")
            while True:
                raw = input().strip()
                try:
                    method = int(raw)
                except ValueError:
                    typer.echo("请输入 1 或 2...")
                    continue
                if method in (1, 2):
                    break
                typer.echo("请输入 1 或 2...")

            if method == 1:
                keep_logged_in_v1()  # 若需要配置：keep_logged_in_v1(cfg)
            else:
                keep_logged_in_v2()  # 若需要配置：keep_logged_in_v2(cfg)

        elif choice in ("no", "n"):
            typer.echo("退出脚本...")
            break
        else:
            typer.echo("请输入 yes 或 no")


@app.command()
def do_logout(
    portalUrl: Optional[str] = typer.Option(
        None, "--portalUrl", help="Portal host/ip, e.g. 10.254.241.19"
    ),
):
    """
    Send logout request and exit.
    """
    try:
        cfg = load_config(None, None, None, portalUrl)
    except Exception as e:
        typer.secho(f"❌ Failed to read config: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    _print_missing(cfg, ["portalUrl"])
    try:
        require_fields(cfg, ["portalUrl"])
    except typer.Exit:
        raise

    try:
        logout(cfg["portalUrl"])
        typer.secho("🥳 已成功发送注销请求！", fg=typer.colors.GREEN)
    except LogoutError as e:
        typer.secho(f"😔 注销失败: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


# 让 `python -m cnc.main` / `python src/cnc/main.py` 也能跑
def main():
    app()


if __name__ == "__main__":
    main()
