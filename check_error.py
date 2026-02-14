#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查错误日志"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 查找最新的失败任务
    task = db.analysis_tasks.find_one(
        {"status": "failed"},
        sort=[("created_at", -1)]
    )
    
    if not task:
        print("No failed task found")
        return 1
    
    print(f"Task ID: {task.get('task_id')}")
    print(f"Stock: {task.get('stock_symbol')}")
    print(f"Status: {task.get('status')}")
    print(f"\nError Message:")
    print(task.get('error_message', 'No error message'))
    
    # 检查result字段
    result = task.get('result', {})
    if result:
        print(f"\nResult:")
        print(json.dumps(result, indent=2, default=str))
    
    client.close()
    return 0

if __name__ == "__main__":
    import json
    import sys
    sys.exit(main())
