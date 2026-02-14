"""测试 _extract_prompts_from_state 方法"""
import sys
sys.path.insert(0, 'd:/trade/TradingAgents-CN')

from app.services.simple_analysis_service import SimpleAnalysisService

# 创建服务实例
service = SimpleAnalysisService()

# 模拟一个包含 request_prompt 的 state
state = {
    'market_report': '市场分析报告内容',
    'fundamentals_report': '基本面分析报告内容',
    'market_request_prompt': '这是市场分析的原始prompt',
    'fundamentals_prompt': '这是基本面分析的原始prompt',
    'messages': []
}

reports = {
    'market_report': '市场分析报告内容',
    'fundamentals_report': '基本面分析报告内容'
}

# 测试提取 prompts
prompts = service._extract_prompts_from_state(state, reports)

print(f"提取的 prompts 数量: {len(prompts)}")
print(f"提取的 prompts 键: {list(prompts.keys())}")

for key, value in prompts.items():
    print(f"\n{key}:")
    print(f"  长度: {len(value)}")
    print(f"  内容: {value[:100]}...")
