"""测试所有工具调用 - 显示完整内容"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

def test_tools():
    toolkit = Toolkit()
    
    test_date = "2026-02-24"
    test_ticker = "600519.SH"
    
    tools_to_test = [
        ("get_market_trend_and_sector", {"ticker": test_ticker, "start_date": test_date, "end_date": test_date}),
        ("get_stock_capital_flow", {"ticker": test_ticker, "start_date": test_date, "end_date": test_date}),
        ("get_stock_sentiment_unified", {"ticker": test_ticker, "curr_date": test_date}),
    ]
    
    for tool_name, tool_args in tools_to_test:
        print(f"\n{'='*80}")
        print(f"工具: {tool_name}")
        print(f"参数: {tool_args}")
        print('='*80)
        
        try:
            tool = getattr(toolkit, tool_name)
            
            if hasattr(tool, 'invoke'):
                result = tool.invoke(tool_args)
            else:
                result = tool(**tool_args)
            
            print(result)
            print()
            
        except Exception as e:
            print(f"错误: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_tools()
