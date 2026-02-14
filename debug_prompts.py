#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试prompts提取问题"""

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
        print(f"Found report")
        
        # Check messages
        messages = report.get("messages", [])
        print(f"\nMessages count: {len(messages)}")
        
        if messages:
            print("\nMessage types:")
            for i, msg in enumerate(messages[:5]):  # First 5 messages
                msg_type = msg.get("type", "unknown") if isinstance(msg, dict) else type(msg).__name__
                content_preview = ""
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    content_preview = content[:50] + "..." if len(content) > 50 else content
                print(f"  [{i}] {msg_type}: {content_preview}")
        
        # Check if any message contains analyst identifiers
        analyst_keywords = ["技术面分析师", "基本面分析师", "Market Analyst", "Fundamentals Analyst"]
        print("\nSearching for analyst identifiers in messages:")
        for i, msg in enumerate(messages):
            if isinstance(msg, dict):
                content = msg.get("content", "")
                for keyword in analyst_keywords:
                    if keyword in content:
                        print(f"  Found '{keyword}' in message {i}")
                        break
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
