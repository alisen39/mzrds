from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional, Any

import tomli_w
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def _default_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    override = os.environ.get("MZRDS_CONFIG_DIR")
    return Path(override) if override else base / "mzrds"


CONFIG_DIR = _default_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.toml"
META_SECTION = "_meta"
META_CURRENT_KEY = "current"


@dataclass
class ConnectionOptions:
    host: str = "127.0.0.1"
    port: int = 6379
    password: Optional[str] = None
    username: Optional[str] = None
    db: int = 0
    uri: Optional[str] = None
    tls: bool = False
    cacert: Optional[str] = None
    cert: Optional[str] = None
    key: Optional[str] = None
    cluster: bool = False

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        # 过滤掉值为 None 的字段，保持配置文件整洁
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ConnectionOptions":
        return cls(**data)


class ConfigStore:
    def __init__(self, file_path: Path = CONFIG_FILE):
        self.file_path = file_path

    def _ensure_dir(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_raw(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        with self.file_path.open("rb") as fh:
            return tomllib.load(fh)

    def _dump_raw(self, data: Dict[str, Any]) -> None:
        self._ensure_dir()
        with self.file_path.open("wb") as fh:
            tomli_w.dump(data, fh)

    def list_profiles(self) -> Dict[str, ConnectionOptions]:
        data = self._load_raw()
        profiles = {}
        for name, value in data.items():
            if name == META_SECTION or not isinstance(value, dict):
                continue
            profiles[name] = ConnectionOptions.from_dict(value)
        return profiles

    def get_profile(self, name: str) -> Optional[ConnectionOptions]:
        data = self._load_raw()
        entry = data.get(name)
        if not isinstance(entry, dict):
            return None
        return ConnectionOptions.from_dict(entry)

    def save_profile(self, name: str, options: ConnectionOptions) -> None:
        data = self._load_raw()
        data[name] = options.to_dict()
        if META_SECTION not in data:
            data[META_SECTION] = {}
        if META_CURRENT_KEY not in data[META_SECTION]:
            data[META_SECTION][META_CURRENT_KEY] = name
        self._dump_raw(data)

    def delete_profile(self, name: str) -> None:
        data = self._load_raw()
        if name in data:
            del data[name]
        meta = data.get(META_SECTION, {})
        if meta.get(META_CURRENT_KEY) == name:
            remaining = [
                key for key in data.keys()
                if key not in (META_SECTION,)
            ]
            if remaining:
                meta[META_CURRENT_KEY] = remaining[0]
            else:
                # 如果没有剩余配置，删除 current 键（而不是设置为 None）
                meta.pop(META_CURRENT_KEY, None)
        data[META_SECTION] = meta
        self._dump_raw(data)

    def get_current(self) -> Optional[str]:
        data = self._load_raw()
        meta = data.get(META_SECTION)
        if not isinstance(meta, dict):
            return None
        return meta.get(META_CURRENT_KEY)

    def set_current(self, name: str) -> None:
        data = self._load_raw()
        if name not in data:
            raise ValueError(f"配置 {name} 不存在")
        meta = data.get(META_SECTION, {})
        meta[META_CURRENT_KEY] = name
        data[META_SECTION] = meta
        self._dump_raw(data)


def merge_options(
    base: Optional[ConnectionOptions],
    overrides: Dict[str, object],
) -> ConnectionOptions:
    data = asdict(base) if base else asdict(ConnectionOptions())
    for key, value in overrides.items():
        if value is None:
            continue
        data[key] = value
    return ConnectionOptions.from_dict(data)


__all__ = [
    "ConnectionOptions",
    "ConfigStore",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "merge_options",
]

