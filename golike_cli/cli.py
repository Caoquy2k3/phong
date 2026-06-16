from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .config import Config, DEFAULT_CONFIG_PATH
from .api import GoLikeClient
from .browser import launch_browser

console = Console()


@click.group()
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=DEFAULT_CONFIG_PATH,
              help="Path to YAML config file")
@click.pass_context
def cli(ctx: click.Context, config_path: Path):
    cfg = Config.load(config_path)
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg


@cli.command()
@click.pass_context
def show_config(ctx: click.Context):
    cfg: Config = ctx.obj["config"]
    table = Table(title="GoLike CLI Config")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("login.login_url", cfg.login.login_url)
    table.add_row("app.headless", str(cfg.app.headless))
    table.add_row("auth.base_api_url", cfg.auth.base_api_url)
    table.add_row("storage_state", str(cfg.storage_state))
    table.add_row("cookies_path", str(cfg.cookies_path))
    console.print(table)


@cli.command(help="Open login page and save storage after you log in")
@click.option("--url", "login_url", type=str, default=None, help="Override login URL")
@click.pass_context
def login(ctx: click.Context, login_url: Optional[str]):
    cfg: Config = ctx.obj["config"]
    if login_url:
        cfg.login.login_url = login_url

    async def run():
        async with launch_browser(
            headless=cfg.app.headless,
            slow_mo_ms=cfg.app.slow_mo_ms,
            user_agent=cfg.app.user_agent,
            viewport_width=cfg.app.viewport_width,
            viewport_height=cfg.app.viewport_height,
            timeout_ms=cfg.app.timeout_ms,
            storage_state=cfg.storage_state,
        ) as (_browser, context, page):
            await page.goto(cfg.login.login_url)
            console.print("Navigate to login and complete authentication...", style="cyan")
            console.print("Press Enter here after finishing login in the browser window.", style="yellow")
            input()
            await context.storage_state(path=str(cfg.storage_state))
            console.print(f"Saved storage state to {cfg.storage_state}", style="green")
    asyncio.run(run())


@cli.group(help="Manage GoLike API auth (token and t)")
@click.pass_context
def auth(ctx: click.Context):
    pass


@auth.command(name="show", help="Show current token/t")
@click.pass_context
def auth_show(ctx: click.Context):
    cfg: Config = ctx.obj["config"]
    token_preview = (cfg.auth.token[:6] + "..." + cfg.auth.token[-4:]) if cfg.auth.token else None
    console.print({
        "base_api_url": cfg.auth.base_api_url,
        "token": token_preview,
        "t": cfg.auth.t,
    })


@auth.command(name="set", help="Set token and optional t, save to config")
@click.option("--token", required=True, help="Bearer token without 'Bearer '")
@click.option("--t", "tval", required=False, help="Optional header t value")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=DEFAULT_CONFIG_PATH)
@click.pass_context
def auth_set(ctx: click.Context, token: str, tval: Optional[str], config_path: Path):
    cfg: Config = ctx.obj["config"]
    cfg.auth.token = token
    cfg.auth.t = tval
    cfg.save(config_path)
    console.print("Saved auth to config", style="green")


@cli.group(help="Instagram endpoints")
@click.pass_context
def ig(ctx: click.Context):
    pass


@ig.command(name="accounts", help="List linked Instagram accounts")
@click.pass_context
def ig_accounts(ctx: click.Context):
    cfg: Config = ctx.obj["config"]
    if not cfg.auth.token:
        console.print("Set token first: auth set --token ...", style="red")
        raise SystemExit(1)
    client = GoLikeClient(base_url=cfg.auth.base_api_url, token=cfg.auth.token, t=cfg.auth.t)
    accounts = client.list_instagram_accounts()
    if not accounts:
        console.print("No accounts found", style="yellow")
        return
    table = Table(title="Instagram Accounts")
    table.add_column("id")
    table.add_column("instagram_username")
    for a in accounts:
        table.add_row(str(a.get("id")), a.get("instagram_username", ""))
    console.print(table)


@ig.command(name="me", help="Show current user profile")
@click.pass_context
def ig_me(ctx: click.Context):
    cfg: Config = ctx.obj["config"]
    if not cfg.auth.token:
        console.print("Set token first: auth set --token ...", style="red")
        raise SystemExit(1)
    client = GoLikeClient(base_url=cfg.auth.base_api_url, token=cfg.auth.token, t=cfg.auth.t)
    me = client.get_me()
    if not me:
        console.print("No user data", style="yellow")
        return
    table = Table(title="User Profile")
    table.add_column("Field")
    table.add_column("Value")
    for k in ("id", "name", "email", "coin"):
        table.add_row(k, str(me.get(k)))
    console.print(table)

@cli.command(help="Take a screenshot of a page")
@click.argument("url")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("screenshot.png"))
@click.pass_context
def screenshot(ctx: click.Context, url: str, out_path: Path):
    cfg: Config = ctx.obj["config"]

    async def run():
        async with launch_browser(
            headless=cfg.app.headless,
            slow_mo_ms=cfg.app.slow_mo_ms,
            user_agent=cfg.app.user_agent,
            viewport_width=cfg.app.viewport_width,
            viewport_height=cfg.app.viewport_height,
            timeout_ms=cfg.app.timeout_ms,
            storage_state=cfg.storage_state,
        ) as (_browser, _context, page):
            await page.goto(url)
            await page.screenshot(path=str(out_path), full_page=True)
            console.print(f"Saved screenshot to {out_path}", style="green")
    asyncio.run(run())


@cli.command(help="Export cookies to JSON")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=None,
              help="Defaults to config cookies_path")
@click.pass_context
def export_cookies(ctx: click.Context, out_path: Optional[Path]):
    cfg: Config = ctx.obj["config"]
    target = out_path or cfg.cookies_path

    async def run():
        async with launch_browser(
            headless=cfg.app.headless,
            slow_mo_ms=cfg.app.slow_mo_ms,
            user_agent=cfg.app.user_agent,
            viewport_width=cfg.app.viewport_width,
            viewport_height=cfg.app.viewport_height,
            timeout_ms=cfg.app.timeout_ms,
            storage_state=cfg.storage_state,
        ) as (_browser, context, _page):
            cookies = await context.cookies()
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            console.print(f"Exported cookies to {target}", style="green")
    asyncio.run(run())


@cli.command(help="GET a URL with Playwright context and print body text")
@click.argument("url")
@click.pass_context
def get(ctx: click.Context, url: str):
    cfg: Config = ctx.obj["config"]

    async def run():
        async with launch_browser(
            headless=cfg.app.headless,
            slow_mo_ms=cfg.app.slow_mo_ms,
            user_agent=cfg.app.user_agent,
            viewport_width=cfg.app.viewport_width,
            viewport_height=cfg.app.viewport_height,
            timeout_ms=cfg.app.timeout_ms,
            storage_state=cfg.storage_state,
        ) as (_browser, _context, page):
            await page.goto(url)
            content = await page.content()
            console.print(f"Fetched {url}, length={len(content)}", style="green")
            # Print a small excerpt to avoid flooding
            console.print(content[:1000])
    asyncio.run(run())


if __name__ == "__main__":
    cli()
