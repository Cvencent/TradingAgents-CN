#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有保存的prompts"""

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
    print(f"Status: {report.get('status')}")
    
    # 检查prompts字段
    prompts = report.get("prompts", {})
    print(f"\n✅ Prompts field ({len(prompts)} items):")
    for key, value in prompts.items():
        if isinstance(value, str):
            print(f"  - {key}: {len(value)} chars")
            # 显示内容预览
            preview = value[:200] if len(value) > 200 else value
            print(f"    Preview: {preview}...")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # 检查state字段中是否有其他prompts
    state = report.get("state", {})
    if isinstance(state, dict):
        prompt_keys = [k for k in state.keys() if 'prompt' in k.lower()]
        if prompt_keys:
            print(f"\n📊 State中的prompt字段 ({len(prompt_keys)} keys):")
            for key in prompt_keys:
                value = state[key]
                if isinstance(value, str):
                    print(f"  - {key}: {len(value)} chars")
                else:
                    print(f"  - {key}: {type(value).__name__}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
