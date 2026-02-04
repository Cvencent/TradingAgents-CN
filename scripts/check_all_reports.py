#!/usr/bin/env python3
"""检查所有报告模块的内容"""

from pymongo import MongoClient

client = MongoClient('mongodb://admin:cwq297297@47.111.20.147:27117/?authSource=admin')
db = client['tradingagents']

task_id = "50f8e5b4-6e62-4fee-a580-735b29bf4f35"

print("=" * 80)
print(f"检查任务: {task_id}")
print("=" * 80)

report = db.analysis_reports.find_one({'task_id': task_id})
if report:
    reports = report.get('reports', {})
    print(f"\n找到 {len(reports)} 个报告模块:")
    
    modules = [
        'bull_researcher', 'bear_researcher', 
        'risky_analyst', 'safe_analyst', 'neutral_analyst',
        'fundamentals_report', 'investment_plan', 'trader_investment_plan',
        'research_team_decision', 'risk_management_decision', 'final_trade_decision'
    ]
    
    for module in modules:
        content = reports.get(module, '')
        content_len = len(content) if content else 0
        print(f"\n{module}:")
        print(f"  长度: {content_len}")
        if content:
            print(f"  内容: {content[:500]}...")
        else:
            print(f"  ⚠️ 内容为空!")
else:
    print("未找到报告")
