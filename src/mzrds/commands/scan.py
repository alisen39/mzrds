from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

import typer

from ..executor import decode_value

if TYPE_CHECKING:
    from ..cli import CLIState


def _client(ctx: typer.Context):
    state: "CLIState" = ctx.obj
    if not state:
        raise typer.Exit(code=1)
    return state.get_client()


def _print_sequence(items: Iterable, with_scores: bool = False) -> None:
    for idx, item in enumerate(items, start=1):
        if with_scores and isinstance(item, tuple):
            key, score = item
            typer.echo(f"{idx}) {decode_value(key)} (score={score})")
        elif isinstance(item, tuple) and len(item) == 2:
            field, value = item
            typer.echo(f"{idx}) {decode_value(field)} => {decode_value(value)}")
        else:
            typer.echo(f"{idx}) {decode_value(item)}")


def _print_page(label: str, cursor: int, items, with_scores: bool = False):
    typer.echo(f"[{label}] cursor={cursor}")
    if not items:
        typer.echo("（无结果）")
        return
    _print_sequence(items, with_scores=with_scores)


def scan_command(
    ctx: typer.Context,
    pattern: str = typer.Option("*", "--pattern", "-p", help="匹配模式"),
    count: int = typer.Option(100, "--count", "-c", help="每次返回的最大条数"),
    cursor: int = typer.Option(0, "--cursor", help="起始游标"),
    auto: bool = typer.Option(False, "--auto", help="自动遍历至末尾"),
) -> None:
    """
    遍历当前数据库的 key 空间 (SCAN)。

    Examples:
      # 列出所有 key (默认显示前 100 个)
      mzrds scan

      # 查找所有以 'user:' 开头的 key，并自动翻页直到结束
      mzrds scan -p "user:*" --auto

      # 每次迭代返回 10 个
      mzrds scan -c 10
    """
    client = _client(ctx)
    if auto:
        iterator = client.scan_iter(match=pattern, count=count)
        _print_sequence(iterator)
    else:
        next_cursor, keys = client.scan(cursor=cursor, match=pattern, count=count)
        _print_page("scan", next_cursor, keys)


def hscan_command(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Hash 键名"),
    pattern: str = typer.Option("*", "--pattern", "-p"),
    count: int = typer.Option(100, "--count", "-c"),
    cursor: int = typer.Option(0, "--cursor"),
    auto: bool = typer.Option(False, "--auto"),
) -> None:
    """
    遍历 Hash 类型的字段 (HSCAN)。

    Examples:
      mzrds hscan myhash
      mzrds hscan myhash -p "field_*" --auto
    """
    client = _client(ctx)
    if auto:
        iterator = client.hscan_iter(key, match=pattern, count=count)
        _print_sequence(iterator)
    else:
        next_cursor, result = client.hscan(key, cursor=cursor, match=pattern, count=count)
        _print_page("hscan", next_cursor, result.items())


def sscan_command(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Set 键名"),
    pattern: str = typer.Option("*", "--pattern", "-p"),
    count: int = typer.Option(100, "--count", "-c"),
    cursor: int = typer.Option(0, "--cursor"),
    auto: bool = typer.Option(False, "--auto"),
) -> None:
    """
    遍历 Set 类型的成员 (SSCAN)。

    Examples:
      mzrds sscan myset
      mzrds sscan myset -p "member_*" --auto
    """
    client = _client(ctx)
    if auto:
        iterator = client.sscan_iter(key, match=pattern, count=count)
        _print_sequence(iterator)
    else:
        next_cursor, result = client.sscan(key, cursor=cursor, match=pattern, count=count)
        _print_page("sscan", next_cursor, result)


def zscan_command(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="ZSet 键名"),
    pattern: str = typer.Option("*", "--pattern", "-p"),
    count: int = typer.Option(100, "--count", "-c"),
    cursor: int = typer.Option(0, "--cursor"),
    auto: bool = typer.Option(False, "--auto"),
    with_scores: bool = typer.Option(True, "--scores/--no-scores", help="显示分数"),
) -> None:
    """
    遍历 Sorted Set 类型的成员 (ZSCAN)。

    Examples:
      mzrds zscan myzset
      mzrds zscan myzset --no-scores
    """
    client = _client(ctx)
    if auto:
        iterator = client.zscan_iter(
            key, match=pattern, count=count, withscores=with_scores
        )
        _print_sequence(iterator, with_scores=with_scores)
    else:
        next_cursor, result = client.zscan(
            key, cursor=cursor, match=pattern, count=count, withscores=with_scores
        )
        _print_page("zscan", next_cursor, result, with_scores=with_scores)


def register_scan_commands(app: typer.Typer) -> None:
    app.command("scan")(scan_command)
    app.command("hscan")(hscan_command)
    app.command("sscan")(sscan_command)
    app.command("zscan")(zscan_command)


__all__ = ["register_scan_commands"]

