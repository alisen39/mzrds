"""测试 scan 命令"""
from __future__ import annotations

import pytest

from mzrds.client import get_client
from mzrds.config import ConnectionOptions


@pytest.mark.integration
def test_scan_basic(redis_options):
    """测试基本 scan 命令"""
    client = get_client(redis_options)
    try:
        # 准备测试数据
        test_keys = [f"test:scan:{i}" for i in range(5)]
        for key in test_keys:
            client.set(key, "value")
        
        # 测试 scan
        cursor, keys = client.scan(cursor=0, match="test:scan:*", count=10)
        assert len(keys) >= 5
        
        # 清理
        for key in test_keys:
            client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_scan_iter(redis_options):
    """测试 scan_iter 自动翻页"""
    client = get_client(redis_options)
    try:
        # 准备测试数据
        test_keys = [f"test:scaniter:{i}" for i in range(10)]
        for key in test_keys:
            client.set(key, "value")
        
        # 测试 scan_iter
        found_keys = list(client.scan_iter(match="test:scaniter:*", count=3))
        assert len(found_keys) >= 10
        
        # 清理
        for key in test_keys:
            client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_hscan(redis_options):
    """测试 hscan 命令"""
    client = get_client(redis_options)
    try:
        key = "test:hscan"
        # 准备测试数据
        fields = {f"field{i}": f"value{i}" for i in range(5)}
        client.hset(key, mapping=fields)
        
        # 测试 hscan
        cursor, result = client.hscan(key, cursor=0, match="field*", count=10)
        assert len(result) >= 5
        
        # 清理
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_hscan_iter(redis_options):
    """测试 hscan_iter 自动翻页"""
    client = get_client(redis_options)
    try:
        key = "test:hscaniter"
        fields = {f"field{i}": f"value{i}" for i in range(10)}
        client.hset(key, mapping=fields)
        
        # 测试 hscan_iter
        found_items = list(client.hscan_iter(key, match="field*", count=3))
        assert len(found_items) >= 10
        
        # 清理
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_sscan(redis_options):
    """测试 sscan 命令"""
    client = get_client(redis_options)
    try:
        key = "test:sscan"
        members = [f"member{i}" for i in range(5)]
        client.sadd(key, *members)
        
        # 测试 sscan
        cursor, result = client.sscan(key, cursor=0, match="member*", count=10)
        assert len(result) >= 5
        
        # 清理
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_sscan_iter(redis_options):
    """测试 sscan_iter 自动翻页"""
    client = get_client(redis_options)
    try:
        key = "test:sscaniter"
        members = [f"member{i}" for i in range(10)]
        client.sadd(key, *members)
        
        # 测试 sscan_iter
        found_members = list(client.sscan_iter(key, match="member*", count=3))
        assert len(found_members) >= 10
        
        # 清理
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_zscan(redis_options):
    """测试 zscan 命令"""
    client = get_client(redis_options)
    try:
        key = "test:zscan"
        members = {f"member{i}": float(i) for i in range(5)}
        client.zadd(key, members)
        
        # 测试 zscan
        cursor, result = client.zscan(key, cursor=0, match="member*", count=10)
        assert len(result) >= 5
        
        # 清理
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_zscan_iter(redis_options):
    """测试 zscan_iter 自动翻页"""
    client = get_client(redis_options)
    try:
        key = "test:zscaniter"
        members = {f"member{i}": float(i) for i in range(10)}
        client.zadd(key, members)
        
        # 测试 zscan_iter
        found_members = list(client.zscan_iter(key, match="member*", count=3))
        assert len(found_members) >= 10
        
        # 清理
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_zscan_with_scores(redis_options):
    """测试 zscan 带分数"""
    client = get_client(redis_options)
    try:
        key = "test:zscanscore"
        members = {"member1": 10.5, "member2": 20.0}
        client.zadd(key, members)
        
        # redis-py 的 zscan 总是返回带分数的列表（元组列表）
        cursor, result = client.zscan(key, cursor=0)
        assert isinstance(result, list)
        assert len(result) >= 2
        # 验证结果是 (member, score) 元组
        assert isinstance(result[0], tuple)
        assert len(result[0]) == 2
        
        # 清理
        client.delete(key)
    finally:
        client.close()

