from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from ..config import ConfigStore, ConnectionOptions

if TYPE_CHECKING:
    from ..cli import CLIState


connection_app = typer.Typer(help="管理 Redis 连接配置")


def _get_store(ctx: typer.Context) -> ConfigStore:
    state = ctx.obj
    if not state:
        raise typer.Exit(code=1)
    return state.store


@connection_app.command("list")
def list_configs(ctx: typer.Context) -> None:
    store = _get_store(ctx)
    profiles = store.list_profiles()
    current = store.get_current()
    if not profiles:
        typer.echo("尚未保存任何连接配置。")
        return
    for name, options in profiles.items():
        prefix = "*" if name == current else " "
        typer.echo(f"{prefix} {name} -> {options.host}:{options.port} (db={options.db})")


@connection_app.command("save")
def save_config(ctx: typer.Context, name: str) -> None:
    state: "CLIState" = ctx.obj
    if not state:
        raise typer.Exit(code=1)
    store = state.store
    options: ConnectionOptions = state.options
    store.save_profile(name, options)
    typer.echo(f"配置 {name} 已保存。")


@connection_app.command("use")
def use_config(ctx: typer.Context, name: str) -> None:
    store = _get_store(ctx)
    if not store.get_profile(name):
        raise typer.BadParameter(f"配置 {name} 不存在")
    store.set_current(name)
    typer.echo(f"已切换到配置 {name}。")


@connection_app.command("delete")
def delete_config(
    ctx: typer.Context,
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="不提示直接删除"),
) -> None:
    store = _get_store(ctx)
    if not force:
        confirm = typer.confirm(f"确认删除配置 {name}？", default=False)
        if not confirm:
            typer.echo("已取消。")
            raise typer.Exit()
    store.delete_profile(name)
    typer.echo(f"配置 {name} 已删除。")


@connection_app.command("show")
def show_config(ctx: typer.Context, name: str | None = typer.Argument(None)) -> None:
    store = _get_store(ctx)
    target = name or store.get_current()
    if not target:
        raise typer.BadParameter("请指定配置名称，或先使用 config use 设定默认连接。")
    profile = store.get_profile(target)
    if not profile:
        raise typer.BadParameter(f"配置 {target} 不存在")
    typer.echo(f"[{target}]")
    for field, value in profile.to_dict().items():
        typer.echo(f"{field} = {value}")

