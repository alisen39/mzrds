from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import typer

from .client import get_client
from .commands.connection import connection_app
from .commands.scan import register_scan_commands
from .config import ConfigStore, ConnectionOptions, merge_options
from .executor import execute_raw, print_response


app = typer.Typer(help="mzrds - 轻量 Redis CLI", add_completion=False)
app.add_typer(connection_app, name="config", help="管理连接配置")
register_scan_commands(app)


@dataclass
class CLIState:
    store: ConfigStore
    options: ConnectionOptions
    active_profile: Optional[str] = None
    _client: Any = None

    def get_client(self):
        if self._client is None:
            self._client = get_client(self.options)
        return self._client

    def close(self) -> None:
        if self._client and hasattr(self._client, "close"):
            self._client.close()


def _collect_overrides(
    host: Optional[str],
    port: Optional[int],
    password: Optional[str],
    username: Optional[str],
    db: Optional[int],
    uri: Optional[str],
    tls: Optional[bool],
    cacert: Optional[str],
    cert: Optional[str],
    key: Optional[str],
    cluster: Optional[bool],
) -> Dict[str, object]:
    overrides: Dict[str, object] = {
        "host": host,
        "port": port,
        "password": password,
        "username": username,
        "db": db,
        "uri": uri,
        "cacert": cacert,
        "cert": cert,
        "key": key,
    }
    if tls is not None:
        overrides["tls"] = tls
    if cluster is not None:
        overrides["cluster"] = cluster
    return overrides


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    use: Optional[str] = typer.Option(
        None, "--use", "-U", help="使用已保存的连接配置"
        ),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Redis 主机"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Redis 端口"),
    password: Optional[str] = typer.Option(None, "--password", "-a", help="认证密码"),
    username: Optional[str] = typer.Option(None, "--user", help="ACL 用户名"),
    db: Optional[int] = typer.Option(None, "--db", "-n", help="数据库编号"),
    uri: Optional[str] = typer.Option(None, "--uri", "-u", help="Redis URI"),
    tls: Optional[bool] = typer.Option(
        None, "--tls/--no-tls", help="启用或关闭 TLS"
    ),
    cacert: Optional[str] = typer.Option(None, "--cacert", help="CA 证书"),
    cert: Optional[str] = typer.Option(None, "--cert", help="客户端证书"),
    key: Optional[str] = typer.Option(None, "--key", help="客户端私钥"),
    cluster: Optional[bool] = typer.Option(
        None, "--cluster/--no-cluster", help="启用 Redis Cluster"
    ),
) -> None:
    store = ConfigStore()
    profile_name = use or store.get_current()
    base = None
    if profile_name:
        base = store.get_profile(profile_name)
        if not base and use:
            raise typer.BadParameter(f"配置 {profile_name} 不存在")
    overrides = _collect_overrides(
        host, port, password, username, db, uri, tls, cacert, cert, key, cluster
    )
    options = merge_options(base, overrides)
    state = CLIState(store=store, options=options, active_profile=profile_name)
    ctx.obj = state

    def _cleanup():
        state.close()

    ctx.call_on_close(_cleanup)

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("exec", help="执行任意 Redis 命令")
def exec_command(
    ctx: typer.Context,
    command: List[str] = typer.Argument(..., metavar="COMMAND", help="Redis 命令及参数"),
) -> None:
    state: CLIState = ctx.obj
    if not state:
        raise typer.Exit(code=1)
    client = state.get_client()
    response = execute_raw(client, command)
    print_response(response)


def run() -> None:
    app()


if __name__ == "__main__":
    run()

