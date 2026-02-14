#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查原始prompt内容"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    task_id = "a5cc5b31-0148-48dd-a37d-5719c8a2cddc"
    
    report = db.analysis_reports.find_one({"task_id": task_id})
    if not report:
        print("Report not found")
        return 1
    
    messages = report.get("messages", [])
    print(f"Total messages: {len(messages)}")
    
    print("\n" + "="*80)
    print("All messages (showing first 300 chars of each):")
    print("="*80)
    
    for i, msg in enumerate(messages):
        if isinstance(msg, dict):
            msg_type = msg.get('type', 'unknown')
            content = msg.get('content', '')
            
            print(f"\n[{i}] Type: {msg_type}")
            if content:
                # 显示内容的前300个字符
                preview = content[:500] if len(content) > 500 else content
                print(f"    Content:\n{preview}")
                if len(content) > 500:
                    print(f"    ... ({len(content)} chars total)")
            else:
                print(f"    (empty content)")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
