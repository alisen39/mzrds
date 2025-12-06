from __future__ import annotations

from typing import Iterable, Sequence

import typer


def decode_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    if isinstance(value, (list, tuple)):
        return [decode_value(v) for v in value]
    if isinstance(value, dict):
        return {decode_value(k): decode_value(v) for k, v in value.items()}
    return value


def execute_raw(client, parts: Sequence[str]):
    if not parts:
        raise typer.BadParameter("需要至少一个 Redis 命令")
    return client.execute_command(*parts)


def print_response(response) -> None:
    decoded = decode_value(response)
    if isinstance(decoded, list):
        for idx, item in enumerate(decoded, start=1):
            typer.echo(f"{idx}) {item}")
    else:
        typer.echo(decoded)


def iter_to_console(items: Iterable) -> None:
    for item in items:
        typer.echo(decode_value(item))


__all__ = ["decode_value", "execute_raw", "print_response", "iter_to_console"]

