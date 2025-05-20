import pytest
import asyncio
from eyesondocs_mcp_server import get_doc_updates, get_usage_stats, search_updates

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# pytestmark = pytest.mark.asyncio  # 移除全局 asyncio 标记

def test_get_doc_updates_basic():
    """测试 get_doc_updates 的基础调用，默认参数。"""
    result = asyncio.run(get_doc_updates())
    assert "分页信息" in result
    assert "更新分割线" in result or "没有找到符合条件的更新" in result

def test_get_doc_updates_invalid_product():
    """测试 get_doc_updates 非法 product 参数。"""
    result = asyncio.run(get_doc_updates(product="INVALID_PRODUCT"))
    assert "无法获取更新数据" in result or "没有找到符合条件的更新" in result

def test_get_doc_updates_weekly():
    """测试 get_doc_updates 周总结类型。"""
    result = asyncio.run(get_doc_updates(update_type="weekly"))
    assert "分页信息" in result
    assert "更新分割线" in result or "没有找到符合条件的更新" in result

def test_search_updates_basic():
    """测试 search_updates 的基础调用。"""
    result = asyncio.run(search_updates(keyword="API"))
    assert "找到" in result or "未找到包含关键词" in result

def test_search_updates_invalid_product():
    """测试 search_updates 非法 product 参数。"""
    result = asyncio.run(search_updates(keyword="API", product="INVALID_PRODUCT"))
    assert "未找到包含关键词" in result or "无法获取更新数据" in result

def test_get_usage_stats_no_password():
    """测试 get_usage_stats 未提供密码。"""
    result = asyncio.run(get_usage_stats())
    assert "需要提供管理员密码" in result 