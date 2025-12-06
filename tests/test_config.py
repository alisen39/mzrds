"""测试配置管理模块"""
from __future__ import annotations

import pytest

from mzrds.config import ConfigStore, ConnectionOptions, merge_options


def test_connection_options_defaults():
    """测试 ConnectionOptions 默认值"""
    opts = ConnectionOptions()
    assert opts.host == "127.0.0.1"
    assert opts.port == 6379
    assert opts.db == 0
    assert opts.password is None
    assert opts.tls is False
    assert opts.cluster is False


def test_connection_options_to_dict(config_store):
    """测试 ConnectionOptions 转字典"""
    opts = ConnectionOptions(host="test.com", port=6380, password="secret")
    data = opts.to_dict()
    assert data["host"] == "test.com"
    assert data["port"] == 6380
    assert data["password"] == "secret"
    # None 值应该被过滤
    assert "username" not in data or data.get("username") is None


def test_connection_options_from_dict():
    """测试从字典创建 ConnectionOptions"""
    data = {"host": "test.com", "port": 6380, "password": "secret"}
    opts = ConnectionOptions.from_dict(data)
    assert opts.host == "test.com"
    assert opts.port == 6380
    assert opts.password == "secret"


def test_config_store_save_and_get(config_store):
    """测试保存和获取配置"""
    opts = ConnectionOptions(host="test.com", port=6380)
    config_store.save_profile("test", opts)
    
    retrieved = config_store.get_profile("test")
    assert retrieved is not None
    assert retrieved.host == "test.com"
    assert retrieved.port == 6380


def test_config_store_list_profiles(config_store):
    """测试列出所有配置"""
    # 先清理可能存在的配置
    for name in list(config_store.list_profiles().keys()):
        config_store.delete_profile(name)
    
    config_store.save_profile("prod", ConnectionOptions(host="prod.com"))
    config_store.save_profile("dev", ConnectionOptions(host="dev.com"))
    
    profiles = config_store.list_profiles()
    assert len(profiles) == 2
    assert "prod" in profiles
    assert "dev" in profiles


def test_config_store_delete_profile(config_store):
    """测试删除配置"""
    config_store.save_profile("test", ConnectionOptions(host="test.com"))
    assert config_store.get_profile("test") is not None
    
    config_store.delete_profile("test")
    assert config_store.get_profile("test") is None


def test_config_store_current_profile(config_store):
    """测试当前配置管理"""
    # 先清理可能存在的配置
    for name in list(config_store.list_profiles().keys()):
        config_store.delete_profile(name)
    
    config_store.save_profile("prod", ConnectionOptions(host="prod.com"))
    config_store.save_profile("dev", ConnectionOptions(host="dev.com"))
    
    config_store.set_current("prod")
    assert config_store.get_current() == "prod"
    
    config_store.set_current("dev")
    assert config_store.get_current() == "dev"


def test_merge_options():
    """测试合并配置选项"""
    base = ConnectionOptions(host="base.com", port=6379, db=0)
    overrides = {"host": "override.com", "db": 1}
    
    merged = merge_options(base, overrides)
    assert merged.host == "override.com"
    assert merged.port == 6379  # 未覆盖的值保持不变
    assert merged.db == 1


def test_merge_options_with_none_base():
    """测试合并配置（无基础配置）"""
    overrides = {"host": "new.com", "port": 6380}
    merged = merge_options(None, overrides)
    assert merged.host == "new.com"
    assert merged.port == 6380
    assert merged.db == 0  # 使用默认值

