#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查messages是否正确保存"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    task_id = "a5cc5b31-0148-48dd-a37d-5719c8a2cddc"
    
    # Check analysis_reports
    print("=== Checking analysis_reports ===")
    report = db.analysis_reports.find_one({"task_id": task_id})
    if report:
        print(f"Found report")
        
        # Check all relevant fields
        print(f"\nFields in report:")
        for key in report.keys():
            value = report[key]
            if isinstance(value, (list, dict)):
                print(f"  - {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"  - {key}: {type(value).__name__}")
        
        # Check messages
        messages = report.get("messages", [])
        print(f"\nMessages count: {len(messages)}")
        
        if messages:
            print("\nFirst 10 messages:")
            for i, msg in enumerate(messages[:10]):
                if isinstance(msg, dict):
                    msg_type = msg.get('type', 'unknown')
                    content_preview = msg.get('content', '')[:80]
                    print(f"  [{i}] {msg_type}: {content_preview}...")
                else:
                    print(f"  [{i}] {type(msg).__name__}: {str(msg)[:80]}...")
        
        # Check prompts
        prompts = report.get("prompts", {})
        print(f"\nPrompts count: {len(prompts)}")
        if prompts:
            for k in prompts.keys():
                print(f"  - {k}")
        
        # Check reports
        reports = report.get("reports", {})
        print(f"\nReports count: {len(reports)}")
        if reports:
            for k in reports.keys():
                print(f"  - {k}")
    else:
        print("Report not found")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
