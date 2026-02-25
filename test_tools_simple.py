"""测试所有工具调用"""
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
    
    results = []
    
    for tool_name, tool_args in tools_to_test:
        print(f"\n{'='*60}")
        print(f"测试工具: {tool_name}")
        print(f"参数: {tool_args}")
        print('='*60)
        
        try:
            tool = getattr(toolkit, tool_name)
            
            if hasattr(tool, 'invoke'):
                print(f"使用 invoke 方法调用")
                result = tool.invoke(tool_args)
            else:
                print(f"使用直接调用")
                result = tool(**tool_args)
            
            result_str = str(result)
            print(f"结果长度: {len(result_str)} 字符")
            print(f"结果:\n{result_str[:800]}...")
            
            results.append({"tool": tool_name, "status": "成功", "length": len(result_str)})
            
        except Exception as e:
            print(f"错误: {type(e).__name__}: {str(e)[:200]}")
            results.append({"tool": tool_name, "status": "失败", "error": str(e)[:100]})
    
    print(f"\n\n{'='*60}")
    print("测试结果汇总")
    print('='*60)
    
    for r in results:
        status_icon = "OK" if r["status"] == "成功" else "X"
        if r["status"] == "成功":
            print(f"[{status_icon}] {r['tool']}: 成功 (结果长度: {r['length']} 字符)")
        else:
            print(f"[{status_ip}] {r['tool']}: 失败 - {r['error']}")

if __name__ == "__main__":
    test_tools()
