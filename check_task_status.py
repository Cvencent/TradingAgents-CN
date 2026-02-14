#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查任务状态"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 查找最新的任务
    task = db.analysis_tasks.find_one(
        {}, 
        sort=[("created_at", -1)]
    )
    
    if not task:
        print("No task found")
        return 1
    
    print(f"Task ID: {task.get('task_id')}")
    print(f"Stock: {task.get('stock_symbol')}")
    print(f"Status: {task.get('status')}")
    print(f"Progress: {task.get('progress', 0)}%")
    print(f"\nParameters:")
    params = task.get('parameters', {})
    print(f"  Selected analysts: {params.get('selected_analysts', [])}")
    
    if task.get('error_message'):
        print(f"\nError: {task.get('error_message')}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
