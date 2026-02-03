#!/usr/bin/env python3
"""
工具测试脚本 - 测试所有Agent使用的工具
生成测试报告到 tool_test_report.md
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试股票列表（A股、港股、美股各一个）
TEST_STOCKS = [
    {"ticker": "000001", "name": "平安银行", "market": "A_SHARE"},
    {"ticker": "0700.HK", "name": "腾讯控股", "market": "HK_STOCK"},
    {"ticker": "AAPL", "name": "苹果公司", "market": "US_STOCK"},
]

results = []

def test_tool(tool_name, func, *args, **kwargs):
    """测试单个工具"""
    print(f"\n{'='*60}")
    print(f"测试工具: {tool_name}")
    print(f"{'='*60}")
    
    result = {
        "tool_name": tool_name,
        "args": str(args),
        "kwargs": str(kwargs),
        "status": "pending",
        "result": "",
        "error": ""
    }
    
    try:
        print(f"参数: args={args}, kwargs={kwargs}")
        output = func(*args, **kwargs)
        result["status"] = "success"
        result["result"] = output[:5000] if output and len(str(output)) > 5000 else str(output)
        print(f"成功 - 结果长度: {len(str(output))}")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"失败: {e}")
    
    return result

def main():
    print("开始测试所有工具...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试股票: {[s['ticker'] for s in TEST_STOCKS]}")
    
    # 导入所有工具
    try:
        from tradingagents.dataflows.interface import (
            get_china_stock_info_unified,
            get_google_news
        )
        print("导入 interface.py 工具成功")
    except Exception as e:
        print(f"导入 interface.py 工具失败: {e}")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        print("导入 agent_utils.py 工具成功")
    except Exception as e:
        print(f"导入 agent_utils.py 工具失败: {e}")
    
    try:
        from tradingagents.utils.stock_utils import StockUtils
        print("导入 StockUtils 工具成功")
    except Exception as e:
        print(f"导入 StockUtils 失败: {e}")
    
    # 测试每个股票
    for stock in TEST_STOCKS:
        ticker = stock["ticker"]
        name = stock["name"]
        market = stock["market"]
        
        print(f"\n{'#'*60}")
        print(f"# 测试股票: {name} ({ticker}) - {market}")
        print(f"{'#'*60}")
        
        stock_result = {
            "stock": ticker,
            "name": name,
            "market": market,
            "market_info": {},
            "tools": []
        }
        
        # 获取市场信息
        try:
            market_info = StockUtils.get_market_info(ticker)
            stock_result["market_info"] = market_info
            print(f"\n市场信息:")
            print(f"  - 是否A股: {market_info.get('is_china', 'N/A')}")
            print(f"  - 是否港股: {market_info.get('is_hk', 'N/A')}")
            print(f"  - 是否美股: {market_info.get('is_us', 'N/A')}")
            print(f"  - 市场名称: {market_info.get('market_name', 'N/A')}")
        except Exception as e:
            print(f"获取市场信息失败: {e}")
        
        # 工具1: get_china_stock_info_unified (仅A股)
        if market_info.get('is_china'):
            tool_result = test_tool(
                "get_china_stock_info_unified",
                get_china_stock_info_unified,
                ticker
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        
        # 工具2: get_stock_fundamentals_unified
        try:
            tool_result = test_tool(
                "get_stock_fundamentals_unified",
                Toolkit.get_stock_fundamentals_unified,
                ticker=ticker,
                curr_date="2026-02-03"
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        except Exception as e:
            print(f"get_stock_fundamentals_unified 工具不存在: {e}")
        
        # 工具3: get_stock_market_data_unified
        try:
            tool_result = test_tool(
                "get_stock_market_data_unified",
                Toolkit.get_stock_market_data_unified,
                ticker=ticker,
                start_date="2025-01-01",
                end_date="2026-02-03"
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        except Exception as e:
            print(f"get_stock_market_data_unified 工具不存在: {e}")
        
        # 工具4: get_stock_news_unified
        try:
            tool_result = test_tool(
                "get_stock_news_unified",
                Toolkit.get_stock_news_unified,
                stock_code=ticker,
                max_news=5
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        except Exception as e:
            print(f"get_stock_news_unified 工具不存在: {e}")
        
        # 工具5: get_stock_sentiment_unified (社交媒体情绪)
        try:
            tool_result = test_tool(
                "get_stock_sentiment_unified",
                Toolkit.get_stock_sentiment_unified,
                stock_code=ticker
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        except Exception as e:
            print(f"get_stock_sentiment_unified 工具不存在: {e}")
        
        # 工具6: get_stock_money_flow_unified
        try:
            tool_result = test_tool(
                "get_stock_money_flow_unified",
                Toolkit.get_stock_money_flow_unified,
                ticker=ticker,
                days=30
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        except Exception as e:
            print(f"get_stock_money_flow_unified 工具不存在: {e}")
        
        # 工具7: get_google_news
        try:
            tool_result = test_tool(
                "get_google_news",
                get_google_news,
                query=ticker,
                curr_date="2026-02-03",
                look_back_days=7
            )
            stock_result["tools"].append(tool_result)
            results.append({**stock_result, "current_tool": tool_result})
        except Exception as e:
            print(f"get_google_news 工具失败: {e}")
    
    # 生成Markdown报告
    generate_markdown_report()
    print(f"\n{'='*60}")
    print("测试完成！报告已生成到 tool_test_report.md")
    print(f"{'='*60}")

def generate_markdown_report():
    """生成Markdown格式的测试报告"""
    
    success_count = sum(1 for r in results if r.get('current_tool', {}).get('status') == 'success')
    error_count = sum(1 for r in results if r.get('current_tool', {}).get('status') == 'error')
    
    md_content = f"""# 工具测试报告

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**测试股票**: {[s['ticker'] for s in TEST_STOCKS]}

---

## 测试摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | {len(results)} |
| 成功 | {success_count} |
| 失败 | {error_count} |

---

## 详细测试结果

"""
    
    # 按股票分组显示结果
    current_stock = None
    for r in results:
        stock = r.get('stock', 'N/A')
        tool = r.get('current_tool', {})
        
        if stock != current_stock:
            md_content += f"\n### 股票: {stock}\n\n"
            md_content += f"**名称**: {r.get('name', 'N/A')}\n\n"
            current_stock = stock
        
        tool_name = tool.get('tool_name', 'N/A')
        status = tool.get('status', 'N/A')
        status_icon = 'SUCCESS' if status == 'success' else 'FAILED'
        
        md_content += f"#### {status_icon} {tool_name}\n\n"
        md_content += f"- **状态**: {status}\n"
        md_content += f"- **参数**: {tool.get('args', '')} {tool.get('kwargs', '')}\n"
        
        if status == 'success':
            result = tool.get('result', '')
            if result:
                # 截断过长的结果
                if len(str(result)) > 2000:
                    result = str(result)[:2000] + "...\n\n_(结果已截断)_"
                md_content += f"\n**结果预览**:\n\n```\n{result}\n```\n"
        else:
            error = tool.get('error', 'N/A')
            md_content += f"- **错误**: {error}\n"
        
        md_content += "\n---\n"
    
    # 添加工具说明
    md_content += """
## 工具列表说明

| 工具名称 | 用途 | 对应分析师 |
|---------|------|-----------|
| get_china_stock_info_unified | 获取A股股票基本信息 | 中国市场分析师 |
| get_stock_fundamentals_unified | 获取统一基本面数据 | 基本面分析师 |
| get_stock_market_data_unified | 获取统一市场数据 | 技术面分析师 |
| get_stock_news_unified | 获取统一新闻数据 | 新闻分析师 |
| get_stock_sentiment_unified | 获取统一情绪数据 | 社交媒体分析师 |
| get_google_news | 获取Google新闻 | 新闻分析师 |
| get_stock_money_flow_unified | 获取资金流向数据 | 资金面分析师 |
| get_stock_market_trend_unified | 获取市场趋势数据 | 市场趋势分析师 |

"""
    
    # 写入文件
    report_path = project_root / "tool_test_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
