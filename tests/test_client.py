"""测试 Redis 客户端连接"""
from __future__ import annotations

import pytest

from mzrds.client import get_client
from mzrds.config import ConnectionOptions


@pytest.mark.integration
def test_create_redis_client(redis_options):
    """测试创建普通 Redis 客户端"""
    client = get_client(redis_options)
    assert client is not None
    
    # 测试连接
    result = client.ping()
    assert result is True
    
    client.close()


@pytest.mark.integration
def test_redis_basic_operations(redis_options):
    """测试基本 Redis 操作"""
    client = get_client(redis_options)
    
    try:
        # 测试 SET/GET
        client.set("test:key", "test_value")
        value = client.get("test:key")
        assert value == b"test_value"
        
        # 测试 DELETE
        client.delete("test:key")
        value = client.get("test:key")
        assert value is None
    finally:
        client.close()


@pytest.mark.integration
def test_redis_hash_operations(redis_options):
    """测试哈希操作"""
    client = get_client(redis_options)
    
    try:
        key = "test:hash"
        client.hset(key, mapping={"field1": "value1", "field2": "value2"})
        
        value1 = client.hget(key, "field1")
        assert value1 == b"value1"
        
        all_fields = client.hgetall(key)
        assert len(all_fields) == 2
        
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_redis_sorted_set_operations(redis_options):
    """测试有序集合操作"""
    client = get_client(redis_options)
    
    try:
        key = "test:zset"
        client.zadd(key, {"member1": 10.5, "member2": 20.0})
        
        count = client.zcard(key)
        assert count == 2
        
        members = client.zrange(key, 0, -1, withscores=True)
        assert len(members) == 2
        
        client.delete(key)
    finally:
        client.close()


@pytest.mark.integration
def test_redis_set_operations(redis_options):
    """测试集合操作"""
    client = get_client(redis_options)
    
    try:
        key = "test:set"
        client.sadd(key, "member1", "member2", "member3")
        
        count = client.scard(key)
        assert count == 3
        
        members = client.smembers(key)
        assert len(members) == 3
        
        client.delete(key)
    finally:
        client.close()

