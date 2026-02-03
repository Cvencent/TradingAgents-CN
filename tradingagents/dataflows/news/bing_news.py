"""
Bing 新闻爬取模块
使用 curl_cffi 模拟真实浏览器访问
"""

import json
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import os
from urllib.parse import quote_plus
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

USE_CURL_CFFI = True
try:
    from curl_cffi import requests as curl_requests
except ImportError:
    USE_CURL_CFFI = False
    import requests as http_requests

from tradingagents.config.runtime_settings import get_float
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

BING_SLEEP_MIN = get_float("TA_BING_NEWS_SLEEP_MIN_SECONDS", "ta_bing_news_sleep_min_seconds", 1.0)
BING_SLEEP_MAX = get_float("TA_BING_NEWS_SLEEP_MAX_SECONDS", "ta_bing_news_sleep_max_seconds", 3.0)


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
)
def make_request(url):
    """Make a request using curl_cffi to simulate real browser"""
    sleep_time = random.uniform(BING_SLEEP_MIN, BING_SLEEP_MAX)
    logger.info(f"[Bing新闻] 等待 {sleep_time:.1f} 秒...")
    time.sleep(sleep_time)

    logger.info(f"[Bing新闻] 发送请求到: {url[:80]}...")

    if USE_CURL_CFFI:
        response = curl_requests.get(
            url,
            impersonate="chrome120",
            timeout=30
        )
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        response = http_requests.get(url, headers=headers, timeout=30)

    logger.info(f"[Bing新闻] 响应状态码: {response.status_code}")
    return response


def getNewsData(query, start_date, end_date):
    """
    Scrape Bing News search results using curl_cffi to bypass anti-bot detection.
    """
    news_results = []
    page = 0
    max_pages = 3

    while page < max_pages:
        offset = page * 10
        encoded_query = quote_plus(query)
        url = (
            f"https://www.bing.com/news/search?q={encoded_query}"
            f"&qft=interval%3d%227%7c%22%20and%20sortby%3d%22date%22"
            f"&first={offset + 1}"
        )

        try:
            response = make_request(url)

            if response.status_code != 200:
                logger.warning(f"[Bing新闻] 响应状态异常: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, "html.parser")

            news_links = soup.select("a[href*='news']")
            seen_links = set()

            for link_elem in news_links[:20]:
                try:
                    href = link_elem.get("href", "")
                    title = link_elem.get_text().strip()

                    if not href or not title:
                        continue

                    if href in seen_links:
                        continue
                    seen_links.add(href)

                    if len(title) < 5 or len(title) > 200:
                        continue

                    if not href.startswith("http"):
                        if href.startswith("/"):
                            href = "https://www.bing.com" + href
                        else:
                            continue

                    news_results.append({
                        "title": title[:150],
                        "link": href,
                        "snippet": f"Bing新闻: {query}",
                        "source": "Bing News",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })

                except Exception as e:
                    logger.warning(f"[Bing新闻] 处理失败: {e}")
                    continue

            if news_results:
                logger.info(f"[Bing新闻] 第{page + 1}页找到 {len(news_results)} 条新闻")
                break

            page += 1

        except Exception as e:
            logger.error(f"[Bing新闻] 获取失败: {e}")
            break

    logger.info(f"[Bing新闻] 获取完成，共 {len(news_results)} 条新闻")
    return news_results


def format_bing_news(news_results, query):
    """
    格式化 Bing 新闻结果为易读的文本格式
    
    Args:
        news_results: list - Bing 新闻列表
        query: str - 搜索关键词
    
    Returns:
        str: 格式化后的新闻文本
    """
    if not news_results:
        return f"未找到与 {query} 相关的新闻"
    
    formatted = f"## {query} Bing 新闻\n\n"
    
    for i, news in enumerate(news_results, 1):
        formatted += f"### {i}. {news.get('title', '无标题')}\n"
        formatted += f"来源: {news.get('source', '未知')} | 日期: {news.get('date', '未知')}\n"
        formatted += f"\n{news.get('snippet', '无摘要')}\n"
        formatted += f"[原文链接]({news.get('link', '')})\n\n"
        formatted += "---\n\n"
    
    return formatted
