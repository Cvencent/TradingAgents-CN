"""测试情绪分析工具 - 打印帖子内容"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

def test_sentiment():
    toolkit = Toolkit()
    
    tool_name = "get_stock_sentiment_unified"
    tool_args = {"ticker": "600519", "curr_date": "2026-02-24"}
    
    print(f"\n{'='*80}")
    print(f"工具: {tool_name}")
    print(f"参数: {tool_args}")
    print('='*80 + "\n")
    
    try:
        tool = getattr(toolkit, tool_name)
        
        if hasattr(tool, 'invoke'):
            result = tool.invoke(tool_args)
        else:
            result = tool(**tool_args)
        
        # 打印完整结果
        print(result)
        
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sentiment()
