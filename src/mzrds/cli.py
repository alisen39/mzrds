from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import typer

from mzrds.client import get_client
from mzrds.commands.connection import connection_app
from mzrds.commands.scan import register_scan_commands
from mzrds.config import ConfigStore, ConnectionOptions, merge_options
from mzrds.executor import execute_raw, print_response


app = typer.Typer(
    help="""
mzrds - 轻量 Redis CLI / Lightweight Redis CLI

无需依赖 redis-cli 即可管理 Redis 连接和执行命令。
支持配置管理、多环境切换、以及 SCAN 系列命令的便捷操作。

Examples:
  # 直接连接并执行命令
  mzrds -h 127.0.0.1 -p 6379 exec info server

  # 保存当前连接配置为 "local"
  mzrds -h 127.0.0.1 save local

  # 使用已保存的配置
  mzrds --use local exec get mykey

  # 扫描所有以 "user:" 开头的 key
  mzrds --use local scan --pattern "user:*" --auto
""",
    add_completion=False,
)
app.add_typer(connection_app, name="config", help="管理连接配置 (list, save, use, delete...)")
register_scan_commands(app)

# ... (rest of the file until exec_command)

@app.command("exec")
def exec_command(
    ctx: typer.Context,
    command: List[str] = typer.Argument(
        ...,
        metavar="COMMAND",
        help="Redis 命令及参数。例如: set key value, get key, info...",
    ),
) -> None:
    """
    执行任意 Redis 命令。

    Examples:
      mzrds exec ping
      mzrds exec set mykey "hello world"
      mzrds exec get mykey
      mzrds exec keys "user:*"
    """
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

