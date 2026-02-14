#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查state中的字段"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 查找最新的报告
    report = db.analysis_reports.find_one(
        {}, 
        sort=[("created_at", -1)]
    )
    
    if not report:
        print("No report found")
        return 1
    
    print(f"Report ID: {report.get('analysis_id')}")
    print(f"Task ID: {report.get('task_id')}")
    print(f"Stock: {report.get('stock_symbol')}")
    
    # 检查prompts字段
    prompts = report.get("prompts", {})
    print(f"\nPrompts field ({len(prompts)} items):")
    for key, value in prompts.items():
        if isinstance(value, str):
            print(f"  - {key}: {len(value)} chars")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # 检查state字段（如果存在）
    if "state" in report:
        state = report["state"]
        print(f"\nState field type: {type(state).__name__}")
        if isinstance(state, dict):
            print(f"\nState keys ({len(state)} keys):")
            for key in sorted(state.keys()):
                value = state[key]
                if isinstance(value, str):
                    print(f"  - {key}: string ({len(value)} chars)")
                elif isinstance(value, (list, dict)):
                    print(f"  - {key}: {type(value).__name__} ({len(value)} items)")
                else:
                    print(f"  - {key}: {type(value).__name__}")
    else:
        print("\nNo state field in report")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
