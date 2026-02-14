#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有可能保存prompt的字段"""

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
    
    print("All fields in report:")
    for key in sorted(report.keys()):
        value = report[key]
        if isinstance(value, (list, dict)):
            print(f"  - {key}: {type(value).__name__} with {len(value)} items")
        elif isinstance(value, str):
            print(f"  - {key}: string ({len(value)} chars)")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # 检查可能包含prompt的字段
    prompt_fields = [
        'prompts', 'prompt', 'system_prompt', 'user_prompt',
        'market_request_prompt', 'fundamentals_request_prompt',
        'sentiment_request_prompt', 'news_request_prompt',
        'raw_prompts', 'request_prompts'
    ]
    
    print("\n" + "="*80)
    print("Checking potential prompt fields:")
    print("="*80)
    
    for field in prompt_fields:
        if field in report:
            value = report[field]
            print(f"\n{field}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, str):
                        print(f"  {k}: {len(v)} chars")
                    else:
                        print(f"  {k}: {type(v).__name__}")
            elif isinstance(value, list):
                print(f"  List with {len(value)} items")
            elif isinstance(value, str):
                print(f"  {value[:200]}...")
            else:
                print(f"  {type(value).__name__}")
    
    # 检查state字段
    if 'state' in report:
        print("\n" + "="*80)
        print("State field contents:")
        print("="*80)
        state = report['state']
        if isinstance(state, dict):
            for key in sorted(state.keys()):
                value = state[key]
                if isinstance(value, str) and len(value) > 100:
                    print(f"\n{key}: {len(value)} chars")
                    print(f"  Preview: {value[:200]}...")
                elif isinstance(value, (list, dict)):
                    print(f"\n{key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"\n{key}: {type(value).__name__}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
