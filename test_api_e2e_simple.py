#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简化的API测试脚本"""

import sys
import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
STOCK_CODE = "000001"

def main():
    # 登录
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                         json={"username": "admin", "password": "admin123"}, timeout=10)
    token = resp.json()["data"]["access_token"]
    print(f"Login OK, token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 启动分析
    resp = requests.post(f"{BASE_URL}/api/analysis/single",
                         json={"stock_code": STOCK_CODE, "analysis_date": "2026-02-11", "parameters": {}},
                         headers=headers, timeout=30)
    print(f"Analysis response: {resp.status_code}")
    task_id = resp.json()["data"]["task_id"]
    print(f"Task ID: {task_id}")

    # 等待并检查状态
    import time
    for i in range(30):
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/api/analysis/tasks/{task_id}/status", headers=headers, timeout=10)
        data = resp.json()["data"]
        status = data["status"]
        progress = data["progress"]
        print(f"[{i+1}] Status: {status}, Progress: {progress}%")
        
        if status in ["completed", "failed"]:
            print(f"\nFinal result:")
            print(json.dumps(data.get("error_message", "No error"), ensure_ascii=False, indent=2))
            
            if status == "completed":
                # 检查prompts
                resp = requests.get(f"{BASE_URL}/api/reports/{task_id}", headers=headers, timeout=10)
                report = resp.json()["data"]
                prompts = report.get("prompts", {})
                print(f"\nPrompts found: {len(prompts)}")
                for k, v in prompts.items():
                    if v:
                        print(f"  {k}: {len(str(v))} chars")
            break

if __name__ == "__main__":
    main()
