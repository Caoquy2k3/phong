from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .config import Config, DEFAULT_CONFIG_PATH
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
