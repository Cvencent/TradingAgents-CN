#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""直接查询数据库检查prompts"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    task_id = "651b584b-bcdf-4586-9178-c0f26f75977d"
    
    # Check analysis_reports
    print("=== Checking analysis_reports ===")
    report = db.analysis_reports.find_one({"task_id": task_id})
    if report:
        print(f"Found report with id: {report.get('_id')}")
        print(f"Keys: {list(report.keys())}")
        if "prompts" in report:
            prompts = report["prompts"]
            print(f"\nPrompts: {len(prompts)} keys")
            for k in prompts.keys():
                print(f"  - {k}: {len(prompts[k])} chars")
        else:
            print("\nNo prompts field in report")
        
        if "messages" in report:
            messages = report["messages"]
            print(f"\nMessages: {len(messages)} items")
        else:
            print("\nNo messages field in report")
    else:
        print("Report not found")
    
    # Check analysis_tasks
    print("\n=== Checking analysis_tasks ===")
    task = db.analysis_tasks.find_one({"task_id": task_id})
    if task:
        print(f"Found task with id: {task.get('_id')}")
        result = task.get("result", {})
        print(f"Result keys: {list(result.keys())}")
        if "prompts" in result:
            prompts = result["prompts"]
            print(f"\nPrompts in result: {len(prompts)} keys")
            for k in prompts.keys():
                print(f"  - {k}: {len(prompts[k])} chars")
        else:
            print("\nNo prompts field in result")
        
        if "messages" in result:
            messages = result["messages"]
            print(f"\nMessages in result: {len(messages)} items")
        else:
            print("\nNo messages field in result")
    else:
        print("Task not found")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
