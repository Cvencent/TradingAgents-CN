"""
同花顺财经新闻爬取模块
用于获取A股股票的相关新闻
"""

import json
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
from urllib.parse import urljoin

try:
    from curl_cffi import requests as curl_requests
    USE_CURL_CFFI = True
except ImportError:
    import requests as http_requests
    USE_CURL_CFFI = False

from tradingagents.config.runtime_settings import get_float
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

THS_SLEEP_MIN = get_float("TA_THS_NEWS_SLEEP_MIN_SECONDS", "ta_ths_news_sleep_min_seconds", 0.5)
THS_SLEEP_MAX = get_float("TA_THS_NEWS_SLEEP_MAX_SECONDS", "ta_ths_news_sleep_max_seconds", 1.5)


def fetch_ths_news_page(symbol, page=1):
    """获取同花顺股票新闻页面"""
    sleep_time = random.uniform(THS_SLEEP_MIN, THS_SLEEP_MAX)
    time.sleep(sleep_time)

    url = f"https://stockpage.10jqka.com.cn/{symbol}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://stockpage.10jqka.com.cn/",
    }

    logger.info(f"[同花顺] 获取 {symbol} 新闻页面...")

    try:
        if USE_CURL_CFFI:
            resp = curl_requests.get(url, headers=headers, impersonate="chrome120", timeout=30)
        else:
            resp = http_requests.get(url, headers=headers, timeout=30)

        logger.info(f"[同花顺] 响应状态: {resp.status_code}")
        return resp

    except Exception as e:
        logger.error(f"[同花顺] 请求失败: {e}")
        return None


def parse_ths_news(soup, symbol):
    """解析同花顺新闻页面"""
    news_items = []

    news_sections = [
        soup.select('div.news-list li'),
        soup.select('ul.news-list li'),
        soup.select('.news_list li'),
        soup.select('div.news-content li'),
        soup.select('.cont_l > ul > li'),
    ]

    news_items = []
    seen_titles = set()

    for section in news_sections:
        for item in section:
            try:
                title_elem = item.find('a') or item
                title = title_elem.get_text().strip() if title_elem else ""

                if not title or len(title) < 5:
                    continue

                if title in seen_titles:
                    continue
                seen_titles.add(title)

                href = title_elem.get('href', '') if title_elem else ""
                if href and not href.startswith('http'):
                    href = urljoin(f"https://stockpage.10jqka.com.cn/{symbol}/", href)

                time_elem = item.find('span') or item.find(class_='time')
                date = ""
                if time_elem:
                    date = time_elem.get_text().strip()

                news_items.append({
                    "title": title[:150],
                    "link": href,
                    "source": "同花顺",
                    "date": date,
                    "summary": ""
                })

            except Exception as e:
                continue

    return news_items


def get_ths_news(symbol, max_items=10):
    """
    获取同花顺股票新闻

    Args:
        symbol: 股票代码（如：300033、000001）
        max_items: 最大返回新闻数量

    Returns:
        list: 新闻列表
    """
    news_results = []

    resp = fetch_ths_news_page(symbol)

    if not resp or resp.status_code != 200:
        logger.warning(f"[同花顺] 获取 {symbol} 新闻失败")
        return news_results

    soup = BeautifulSoup(resp.content, 'html.parser')
    news_results = parse_ths_news(soup, symbol)

    logger.info(f"[同花顺] 获取到 {len(news_results)} 条新闻")

    if len(news_results) > max_items:
        news_results = news_results[:max_items]

    return news_results


def format_ths_news(news_results, symbol):
    """
    格式化同花顺新闻为易读的文本

    Args:
        news_results: list - 新闻列表
        symbol: str - 股票代码

    Returns:
        str: 格式化后的新闻文本
    """
    if not news_results:
        return f"未找到 {symbol} 的相关新闻"

    formatted = f"## {symbol} 同花顺财经新闻\n\n"

    for i, news in enumerate(news_results, 1):
        formatted += f"### {i}. {news.get('title', '无标题')}\n"
        if news.get('date'):
            formatted += f"**时间**: {news.get('date', '')}\n"
        formatted += f"**来源**: {news.get('source', '同花顺')}\n"
        if news.get('link'):
            formatted += f"[阅读原文]({news.get('link', '')})\n"
        formatted += "\n---\n\n"

    return formatted


def get_ths_news_api(symbol, page=1):
    """尝试使用同花顺 API 获取新闻"""
    url = f"https://datacenter.10jqka.com.cn/api/stock/news"
    params = {
        "symbol": symbol,
        "page": page
    }

    try:
        if USE_CURL_CFFI:
            resp = curl_requests.get(url, params=params, impersonate="chrome120", timeout=30)
        else:
            resp = http_requests.get(url, params=params, timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                return data.get("data", [])
    except Exception as e:
        logger.warning(f"[同花顺] API 获取失败: {e}")

    return None
