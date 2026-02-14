#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查任务配置"""

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
    
    # 检查parameters
    params = task.get('parameters', {})
    print(f"\n📋 Parameters:")
    for key, value in params.items():
        print(f"  - {key}: {value}")
    
    # 检查selected_analysts
    selected = params.get('selected_analysts', [])
    print(f"\n🔍 Selected analysts: {selected}")
    
    # 检查include_sentiment和include_news
    print(f"\n📊 Include sentiment: {params.get('include_sentiment', False)}")
    print(f"📰 Include news: {params.get('include_news', False)}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
