"""测试命令执行器"""
from __future__ import annotations

import pytest

from mzrds.executor import decode_value, execute_raw
from mzrds.client import get_client
from mzrds.config import ConnectionOptions


@pytest.mark.integration
def test_execute_raw_ping(redis_options):
    """测试执行 PING 命令"""
    client = get_client(redis_options)
    try:
        result = execute_raw(client, ["PING"])
        # redis-py 的 execute_command 对 PING 做了特殊处理，返回 True
        assert result is True or result == b"PONG"
    finally:
        client.close()


@pytest.mark.integration
def test_execute_raw_set_get(redis_options):
    """测试执行 SET/GET 命令"""
    client = get_client(redis_options)
    try:
        execute_raw(client, ["SET", "test:exec", "hello"])
        result = execute_raw(client, ["GET", "test:exec"])
        assert result == b"hello"
        
        client.delete("test:exec")
    finally:
        client.close()


@pytest.mark.integration
def test_execute_raw_hgetall(redis_options):
    """测试执行 HGETALL 命令"""
    client = get_client(redis_options)
    try:
        key = "test:hash:exec"
        client.hset(key, mapping={"a": "1", "b": "2"})
        
        result = execute_raw(client, ["HGETALL", key])
        # redis-py 的 execute_command 对 HGETALL 做了特殊处理，返回字典
        assert isinstance(result, (list, dict))
        if isinstance(result, dict):
            assert len(result) == 2
            assert result.get(b"a") == b"1"
            assert result.get(b"b") == b"2"
        else:
            assert len(result) == 4  # 字段和值交替
        
        client.delete(key)
    finally:
        client.close()


def test_decode_value_bytes():
    """测试解码字节值"""
    from mzrds.executor import decode_value
    
    assert decode_value(b"hello") == "hello"
    assert decode_value(b"\xff\xfe") == "fffe"  # 无法解码的字节转为 hex


def test_decode_value_list():
    """测试解码列表"""
    from mzrds.executor import decode_value
    
    result = decode_value([b"a", b"b", b"c"])
    assert result == ["a", "b", "c"]


def test_decode_value_dict():
    """测试解码字典"""
    from mzrds.executor import decode_value
    
    result = decode_value({b"key1": b"value1", b"key2": b"value2"})
    assert result == {"key1": "value1", "key2": "value2"}

