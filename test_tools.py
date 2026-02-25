import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

toolkit = Toolkit()

def test_market_data():
    print("=" * 60)
    print("测试 get_stock_market_data_unified (技术面)")
    print("=" * 60)
    try:
        tool = toolkit.get_stock_market_data_unified
        result = tool.invoke({"ticker": "300033", "start_date": "2026-02-13", "end_date": "2026-02-13"})
        print(f"结果长度: {len(result)}")
        print(f"前500字符:\n{result[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_fundamentals():
    print("=" * 60)
    print("测试 get_stock_fundamentals_unified (基本面)")
    print("=" * 60)
    try:
        tool = toolkit.get_stock_fundamentals_unified
        result = tool.invoke({"ticker": "300033", "start_date": "2026-02-13", "end_date": "2026-02-13", "curr_date": "2026-02-13"})
        print(f"结果长度: {len(result)}")
        print(f"前500字符:\n{result[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_capital_flow():
    print("=" * 60)
    print("测试 get_stock_capital_flow (资金流)")
    print("=" * 60)
    try:
        tool = toolkit.get_stock_capital_flow
        result = tool("300033", "2026-02-13", "2026-02-13")
        print(f"结果长度: {len(result)}")
        print(f"前500字符:\n{result[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_news():
    print("=" * 60)
    print("测试 get_stock_news_unified (新闻)")
    print("=" * 60)
    try:
        tool = toolkit.get_stock_news_unified
        result = tool("300033", "2026-02-13")
        print(f"结果长度: {len(result)}")
        print(f"前500字符:\n{result[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_sentiment():
    print("=" * 60)
    print("测试 get_stock_sentiment_unified (社媒)")
    print("=" * 60)
    try:
        tool = toolkit.get_stock_sentiment_unified
        result = tool.invoke({"ticker": "300033", "curr_date": "2026-02-13"})
        print(f"结果长度: {len(result)}")
        print(f"前500字符:\n{result[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_market_trend():
    print("=" * 60)
    print("测试 get_market_trend_and_sector (大盘走势)")
    print("=" * 60)
    try:
        tool = toolkit.get_market_trend_and_sector
        result = tool("300033", "2026-02-10", "2026-02-13")
        print(f"结果长度: {len(result)}")
        print(f"前500字符:\n{result[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

if __name__ == "__main__":
    test_market_data()
    test_fundamentals()
    test_capital_flow()
    test_news()
    test_sentiment()
    test_market_trend()
