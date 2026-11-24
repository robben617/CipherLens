"""Tavily 联网搜索：只做一次检索，结果仅本次请求使用，不落库、不记 key。"""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("cipherlens.search")

TAVILY_URL = "https://api.tavily.com/search"
MAX_RESULTS = 5
CONTENT_LIMIT = 240


class SearchUnavailable(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


def _clean_item(item) -> dict | None:
    if not isinstance(item, dict):
        return None
    url = item.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return None
    title = item.get("title")
    content = item.get("content")
    domain = _domain(url)
    return {
        "title": (title if isinstance(title, str) else domain)[:120],
        "url": url[:500],
        "domain": domain[:80],
        "content": (content if isinstance(content, str) else "").strip()[:CONTENT_LIMIT],
    }


async def search(query: str, max_results: int = MAX_RESULTS, timeout: float = 12.0):
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise SearchUnavailable("search_disabled", "后端未配置 Tavily Key，联网搜索暂不可用")

    body = {
        "api_key": key,
        "query": query.strip()[:400],
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(5.0, timeout))
        ) as client:
            response = await client.post(TAVILY_URL, json=body)
    except httpx.TimeoutException as error:
        raise SearchUnavailable("search_timeout", "联网搜索超时") from error
    except httpx.HTTPError as error:
        raise SearchUnavailable("search_network", "连不上搜索服务") from error

    if response.status_code in (401, 403):
        raise SearchUnavailable("search_unauthorized", "搜索 Key 无效或没有权限")
    if response.status_code == 429:
        raise SearchUnavailable("search_rate_limited", "搜索额度用尽或请求过于频繁")
    if response.status_code != 200:
        raise SearchUnavailable(f"search_http_{response.status_code}", f"搜索服务返回 {response.status_code}")

    try:
        payload = response.json()
    except ValueError as error:
        raise SearchUnavailable("search_bad_payload", "搜索服务返回了无法解析的内容") from error

    results = [
        cleaned
        for item in payload.get("results") or []
        if (cleaned := _clean_item(item)) is not None
    ][:max_results]
    if not results:
        raise SearchUnavailable("search_empty", "没有搜到相关网页")

    logger.info("web search results=%s query_len=%s", len(results), len(query))
    return {"query": query, "results": results}