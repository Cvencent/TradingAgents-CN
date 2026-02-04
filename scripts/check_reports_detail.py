#!/usr/bin/env python3
"""检查报告详情"""

from pymongo import MongoClient

client = MongoClient('mongodb://admin:cwq297297@47.111.20.147:27117/?authSource=admin')
db = client['tradingagents']

task_id = "50f8e5b4-6e62-4fee-a580-735b29bf4f35"

print("=" * 80)
print(f"检查任务: {task_id}")
print("=" * 80)

# 检查 analysis_tasks
task = db.analysis_tasks.find_one({'task_id': task_id})
if task:
    print("\n[analysis_tasks] 找到任务")
    result = task.get('result', {})
    reports = result.get('reports', {})
    print(f"  result.reports 键: {list(reports.keys())}")
else:
    print("\n[analysis_tasks] 未找到任务")

# 检查 analysis_reports
report = db.analysis_reports.find_one({'task_id': task_id})
if report:
    print("\n[analysis_reports] 找到报告")
    reports = report.get('reports', {})
    print(f"  reports 键: {list(reports.keys())}")
    
    # 检查bull_researcher内容
    bull = reports.get('bull_researcher', '')
    bear = reports.get('bear_researcher', '')
    risky = reports.get('risky_analyst', '')
    safe = reports.get('safe_analyst', '')
    neutral = reports.get('neutral_analyst', '')
    
    print(f"\n  bull_researcher 长度: {len(bull)}")
    print(f"  bear_researcher 长度: {len(bear)}")
    print(f"  risky_analyst 长度: {len(risky)}")
    print(f"  safe_analyst 长度: {len(safe)}")
    print(f"  neutral_analyst 长度: {len(neutral)}")
    
    if bull:
        print(f"\n  bull_researcher 预览: {bull[:200]}...")
else:
    print("\n[analysis_reports] 未找到报告")
