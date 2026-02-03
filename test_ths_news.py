#!/usr/bin/env python3
"""
同花顺财经新闻测试脚本
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os
os.environ['TA_DISABLE_LOGGING'] = 'true'

from tradingagents.dataflows.news.ths_news import get_ths_news, format_ths_news

def main():
    print("=" * 60)
    print("同花顺财经新闻测试")
    print("=" * 60)

    test_stocks = [
        ("300033", "300033"),
        ("000001", "000001"),
        ("600000", "600000"),
    ]

    for symbol, name in test_stocks:
        print(f"\n测试股票: {symbol} ({name})")
        print("-" * 40)

        news = get_ths_news(symbol)

        if news:
            print(f"获取到 {len(news)} 条新闻")
            print("\n前5条新闻:")
            for i, item in enumerate(news[:5], 1):
                title = item.get('title', '无标题')[:40]
                date = item.get('date', '')
                print(f"{i}. {title}... [{date}]")
        else:
            print("未获取到新闻")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
