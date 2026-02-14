#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查新任务的prompts"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    task_id = "65b79c54-d5f4-4f74-ae07-962c83991cbf"
    
    report = db.analysis_reports.find_one({"task_id": task_id})
    if not report:
        print("Report not found")
        return 1
    
    print("Report fields:")
    for key in sorted(report.keys()):
        value = report[key]
        if isinstance(value, (list, dict)):
            print(f"  - {key}: {type(value).__name__} with {len(value)} items")
        elif isinstance(value, str):
            print(f"  - {key}: string ({len(value)} chars)")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # 检查prompts字段
    prompts = report.get("prompts", {})
    print(f"\nPrompts field:")
    if prompts:
        for key, value in prompts.items():
            if isinstance(value, str):
                print(f"  - {key}: {len(value)} chars")
                print(f"    Preview: {value[:200]}...")
            else:
                print(f"  - {key}: {type(value).__name__}")
    else:
        print("  (empty)")
    
    # 检查state字段
    state = report.get("state", {})
    print(f"\nState field:")
    if isinstance(state, dict):
        for key in sorted(state.keys()):
            value = state[key]
            if isinstance(value, str) and len(value) > 50:
                print(f"  - {key}: string ({len(value)} chars)")
            elif isinstance(value, (list, dict)):
                print(f"  - {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"  - {key}: {type(value).__name__}")
    else:
        print(f"  type: {type(state).__name__}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
