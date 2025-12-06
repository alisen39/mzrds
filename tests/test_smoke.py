"""冒烟测试和性能测试"""
from __future__ import annotations

import time
from typing import List, Tuple

import pytest

from mzrds.client import get_client
from mzrds.config import ConnectionOptions


@pytest.fixture
def redis_options():
    """Redis 连接选项"""
    return ConnectionOptions(
        host="192.168.31.12",
        port=6379,
        db=0,
    )


@pytest.fixture
def test_prefix():
    """测试数据前缀"""
    return f"smoke_test_{int(time.time())}"


@pytest.fixture(autouse=True)
def cleanup_test_data(redis_options, test_prefix):
    """自动清理测试数据"""
    client = get_client(redis_options)
    try:
        yield
    finally:
        # 清理所有测试数据
        keys_to_delete = []
        for key in client.scan_iter(match=f"{test_prefix}:*"):
            keys_to_delete.append(key)
        
        if keys_to_delete:
            # 分批删除，避免一次性删除太多
            batch_size = 1000
            for i in range(0, len(keys_to_delete), batch_size):
                batch = keys_to_delete[i:i + batch_size]
                client.delete(*batch)
        
        client.close()


@pytest.mark.smoke
def test_generate_large_dataset(redis_options, test_prefix):
    """生成大量测试数据"""
    client = get_client(redis_options)
    try:
        # 生成 10,000 条数据
        data_count = 10000
        key = f"{test_prefix}:zset:large"
        
        print(f"\n生成 {data_count} 条数据到 {key}...")
        start_time = time.time()
        
        # 批量写入数据
        batch_size = 1000
        members = {}
        for i in range(data_count):
            members[f"member_{i:06d}"] = float(i)
            if len(members) >= batch_size:
                client.zadd(key, members)
                members = {}
        
        # 写入剩余数据
        if members:
            client.zadd(key, members)
        
        elapsed = time.time() - start_time
        print(f"数据生成完成，耗时: {elapsed:.2f} 秒")
        
        # 验证数据量
        count = client.zcard(key)
        assert count == data_count, f"期望 {data_count} 条数据，实际 {count} 条"
        print(f"验证通过：实际数据量 {count} 条")
        
    finally:
        client.close()


@pytest.mark.smoke
def test_zscan_performance_with_large_dataset(redis_options, test_prefix):
    """测试 zscan 在大数据集下的性能"""
    client = get_client(redis_options)
    try:
        key = f"{test_prefix}:zset:large"
        data_count = 10000
        
        # 先生成数据
        print(f"\n准备测试数据：{data_count} 条...")
        members = {}
        batch_size = 1000
        for i in range(data_count):
            members[f"member_{i:06d}"] = float(i)
            if len(members) >= batch_size:
                client.zadd(key, members)
                members = {}
        if members:
            client.zadd(key, members)
        
        # 测试 1: 单次 zscan（不自动翻页）
        print("\n测试 1: 单次 zscan（count=100）...")
        start_time = time.time()
        cursor, result = client.zscan(key, cursor=0, count=100)
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.4f} 秒，返回 {len(result)} 条数据")
        # Redis 的 count 是提示值，实际返回可能略多（通常不超过 10%）
        assert len(result) > 0 and len(result) <= 150, f"单次 scan 返回数量异常: {len(result)}"
        
        # 测试 2: zscan_iter 自动翻页（遍历所有数据）
        print("\n测试 2: zscan_iter 自动翻页（遍历所有数据）...")
        start_time = time.time()
        all_members = list(client.zscan_iter(key, count=100))
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.2f} 秒，遍历 {len(all_members)} 条数据")
        print(f"  平均速度: {len(all_members) / elapsed:.0f} 条/秒")
        assert len(all_members) == data_count, f"应该遍历所有 {data_count} 条数据"
        
        # 测试 3: 带模式匹配的 zscan_iter
        print("\n测试 3: zscan_iter 带模式匹配（member_*000）...")
        start_time = time.time()
        matched_members = list(client.zscan_iter(key, match="member_*000", count=100))
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.4f} 秒，匹配 {len(matched_members)} 条数据")
        # 应该匹配 member_0000, member_1000, member_2000, ... member_9000，共 10 条
        assert len(matched_members) == 10, f"应该匹配 10 条数据，实际 {len(matched_members)} 条"
        
    finally:
        client.close()


@pytest.mark.smoke
def test_multiple_zsets_performance(redis_options, test_prefix):
    """测试多个 zset 的性能"""
    client = get_client(redis_options)
    try:
        zset_count = 10
        data_per_zset = 1000
        
        print(f"\n生成 {zset_count} 个 zset，每个 {data_per_zset} 条数据...")
        start_time = time.time()
        
        for zset_idx in range(zset_count):
            key = f"{test_prefix}:zset:{zset_idx}"
            members = {f"m_{i}": float(i) for i in range(data_per_zset)}
            client.zadd(key, members)
        
        elapsed = time.time() - start_time
        print(f"数据生成完成，耗时: {elapsed:.2f} 秒")
        
        # 测试遍历所有 zset
        print(f"\n遍历所有 {zset_count} 个 zset...")
        start_time = time.time()
        total_members = 0
        for zset_idx in range(zset_count):
            key = f"{test_prefix}:zset:{zset_idx}"
            members = list(client.zscan_iter(key, count=100))
            total_members += len(members)
        
        elapsed = time.time() - start_time
        print(f"遍历完成，耗时: {elapsed:.2f} 秒，总计 {total_members} 条数据")
        print(f"平均速度: {total_members / elapsed:.0f} 条/秒")
        
        assert total_members == zset_count * data_per_zset
        
    finally:
        client.close()


@pytest.mark.smoke
def test_scan_commands_performance(redis_options, test_prefix):
    """测试所有 scan 命令的性能"""
    client = get_client(redis_options)
    try:
        data_count = 5000
        
        # 准备不同类型的数据
        print(f"\n准备测试数据：{data_count} 条...")
        
        # 1. 普通 keys
        for i in range(data_count):
            client.set(f"{test_prefix}:key:{i}", f"value_{i}")
        
        # 2. Hash
        hash_key = f"{test_prefix}:hash:large"
        hash_fields = {f"field_{i}": f"value_{i}" for i in range(data_count)}
        batch_size = 1000
        for i in range(0, data_count, batch_size):
            batch = dict(list(hash_fields.items())[i:i + batch_size])
            client.hset(hash_key, mapping=batch)
        
        # 3. Set
        set_key = f"{test_prefix}:set:large"
        set_members = [f"member_{i}" for i in range(data_count)]
        for i in range(0, data_count, batch_size):
            batch = set_members[i:i + batch_size]
            client.sadd(set_key, *batch)
        
        # 4. ZSet
        zset_key = f"{test_prefix}:zset:large"
        zset_members = {f"member_{i}": float(i) for i in range(data_count)}
        for i in range(0, data_count, batch_size):
            batch = dict(list(zset_members.items())[i:i + batch_size])
            client.zadd(zset_key, batch)
        
        print("数据准备完成，开始性能测试...\n")
        
        # 测试 scan
        print("测试 scan...")
        start_time = time.time()
        keys = list(client.scan_iter(match=f"{test_prefix}:key:*", count=100))
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.2f} 秒，遍历 {len(keys)} 个 key")
        
        # 测试 hscan
        print("测试 hscan...")
        start_time = time.time()
        hash_items = list(client.hscan_iter(hash_key, count=100))
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.2f} 秒，遍历 {len(hash_items)} 个字段")
        
        # 测试 sscan
        print("测试 sscan...")
        start_time = time.time()
        set_items = list(client.sscan_iter(set_key, count=100))
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.2f} 秒，遍历 {len(set_items)} 个成员")
        
        # 测试 zscan
        print("测试 zscan...")
        start_time = time.time()
        zset_items = list(client.zscan_iter(zset_key, count=100))
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.2f} 秒，遍历 {len(zset_items)} 个成员")
        
        # 验证
        assert len(keys) == data_count
        assert len(hash_items) == data_count
        assert len(set_items) == data_count
        assert len(zset_items) == data_count
        
    finally:
        client.close()


@pytest.mark.smoke
def test_zscan_with_different_count_values(redis_options, test_prefix):
    """测试不同 count 值对 zscan 性能的影响"""
    client = get_client(redis_options)
    try:
        data_count = 10000
        key = f"{test_prefix}:zset:count_test"
        
        # 生成数据
        print(f"\n生成 {data_count} 条测试数据...")
        members = {}
        for i in range(data_count):
            members[f"m_{i}"] = float(i)
            if len(members) >= 1000:
                client.zadd(key, members)
                members = {}
        if members:
            client.zadd(key, members)
        
        # 测试不同的 count 值
        count_values = [10, 100, 500, 1000]
        print("\n测试不同 count 值的性能：")
        
        for count in count_values:
            start_time = time.time()
            all_members = list(client.zscan_iter(key, count=count))
            elapsed = time.time() - start_time
            speed = len(all_members) / elapsed if elapsed > 0 else 0
            print(f"  count={count:4d}: 耗时 {elapsed:.2f} 秒，速度 {speed:.0f} 条/秒")
            assert len(all_members) == data_count
        
    finally:
        client.close()

