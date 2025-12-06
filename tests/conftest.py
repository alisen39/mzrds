"""pytest 配置和共享 fixtures"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from mzrds.config import ConfigStore, ConnectionOptions


@pytest.fixture
def temp_config_dir():
    """创建临时配置目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "mzrds"
        config_file = config_dir / "config.toml"
        original_env = os.environ.get("MZRDS_CONFIG_DIR")
        os.environ["MZRDS_CONFIG_DIR"] = str(config_dir)
        yield config_dir
        if original_env:
            os.environ["MZRDS_CONFIG_DIR"] = original_env
        elif "MZRDS_CONFIG_DIR" in os.environ:
            del os.environ["MZRDS_CONFIG_DIR"]


@pytest.fixture
def config_store(temp_config_dir):
    """创建配置存储实例"""
    return ConfigStore()


@pytest.fixture
def redis_options():
    """Redis 连接选项"""
    return ConnectionOptions(
        host="192.168.31.12",
        port=6379,
        db=0,
    )

