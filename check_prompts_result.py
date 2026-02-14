#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有分析师的prompts结果"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 查找最新的完成报告
    report = db.analysis_reports.find_one(
        {"status": "completed"},
        sort=[("created_at", -1)]
    )
    
    if not report:
        print("No completed report found")
        return 1
    
    print(f"Report ID: {report.get('analysis_id')}")
    print(f"Task ID: {report.get('task_id')}")
    print(f"Stock: {report.get('stock_symbol')}")
    
    # 检查prompts字段
    prompts = report.get("prompts", {})
    print(f"\n✅ Prompts field ({len(prompts)} items):")
    for key, value in prompts.items():
        if isinstance(value, str):
            print(f"  - {key}: {len(value)} chars")
            preview = value[:150] if len(value) > 150 else value
            print(f"    Preview: {preview}...")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # 检查reports字段
    reports = report.get("reports", {})
    print(f"\n📊 Reports field ({len(reports)} items):")
    for key in reports.keys():
        print(f"  - {key}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
