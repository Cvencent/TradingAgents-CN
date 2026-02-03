#!/usr/bin/env python3
"""
Bing 新闻获取测试脚本
"""

import sys
import time
from pathlib import Path
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 禁用日志模块避免编码问题
import os
os.environ['TA_DISABLE_LOGGING'] = 'true'

try:
    from curl_cffi import requests as curl_requests
    USE_CURL_CFFI = True
    print("[OK] curl_cffi available")
except ImportError:
    USE_CURL_CFFI = False
    import requests as http_requests
    print("[WARN] curl_cffi not available, using requests")

from datetime import datetime

def get_bing_news(query, max_pages=2):
    """获取 Bing 新闻"""
    news_results = []
    
    for page in range(max_pages):
        offset = page * 10
        encoded_query = quote_plus(query)
        url = (
            f"https://www.bing.com/news/search?q={encoded_query}"
            f"&qft=interval%3d%227%7c%22%20and%20sortby%3d%22date%22"
            f"&first={offset + 1}"
        )
        
        print(f"\n[{page + 1}] 发送请求: {url[:80]}...")
        
        try:
            if USE_CURL_CFFI:
                response = curl_requests.get(
                    url,
                    impersonate="chrome120",
                    timeout=30
                )
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                }
                response = http_requests.get(url, headers=headers, timeout=30)
            
            print(f"    状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"    异常状态码，停止")
                break
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 查找所有新闻链接
            news_links = soup.select("a[href]")
            seen_links = set()
            page_count = 0
            
            for link_elem in news_links:
                try:
                    href = link_elem.get("href", "").strip()
                    title = link_elem.get_text().strip()
                    
                    if not href or not title:
                        continue
                    
                    if href in seen_links:
                        continue
                    seen_links.add(href)
                    
                    # 过滤有效新闻链接
                    if len(title) < 10 or len(title) > 200:
                        continue
                    
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]
                    
                    if not href.startswith("http"):
                        continue
                    
                    # 跳过 Bing 自己的链接
                    if "bing.com" in href:
                        continue
                    
                    news_results.append({
                        "title": title[:150],
                        "link": href[:500],
                        "query": query,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    page_count += 1
                    
                    if page_count >= 10:
                        break
                        
                except Exception as e:
                    continue
            
            print(f"    找到 {page_count} 条新闻")
            
            if page_count == 0:
                break
                
        except Exception as e:
            print(f"    请求失败: {e}")
            break
        
        # 避免请求过快
        time.sleep(2)
    
    return news_results

def main():
    print("=" * 60)
    print("Bing 新闻获取测试")
    print("=" * 60)
    
    test_queries = [
        "300033 股票",
        "A股 财报",
        "中国股市 新闻",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"测试查询: {query}")
        print("=" * 60)
        
        news = get_bing_news(query)
        
        print(f"\n获取结果: {len(news)} 条新闻")
        
        if news:
            print("\n前5条新闻:")
            for i, item in enumerate(news[:5], 1):
                print(f"{i}. {item['title'][:60]}...")
                print(f"   {item['link'][:60]}...")
        else:
            print("  未获取到新闻")
        
        print()
        time.sleep(3)

if __name__ == "__main__":
    main()
