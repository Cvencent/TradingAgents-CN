#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查任务状态和prompts"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def main():
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"username": "admin", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    task_id = "651b584b-bcdf-4586-9178-c0f26f75977d"
    
    # Wait for completion
    print("Waiting for task to complete...")
    for i in range(60):
        time.sleep(5)
        resp = requests.get(f"{BASE_URL}/api/analysis/tasks/{task_id}/status", headers=headers)
        data = resp.json()["data"]
        status = data["status"]
        progress = data.get("progress", 0)
        print(f"  [{i*5+5}s] {status} ({progress}%)")
        if status == "completed":
            print("Task completed!")
            break
        elif status == "failed":
            print(f"Task failed! Error: {data.get('error_message', 'Unknown')}")
            break
    
    # Check prompts
    print("\nChecking prompts...")
    resp = requests.get(f"{BASE_URL}/api/reports/{task_id}/prompts", headers=headers)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    data = result.get("data", {})
    print(f"Prompts count: {len(data.get('prompts', []))}")
    print(f"Prompts by step count: {len(data.get('prompts_by_step', {}))}")
    if data.get("warning"):
        print(f"Warning: {data.get('warning')}")
    
    # Show prompts summary
    prompts = data.get("prompts", [])
    if prompts:
        print("\nPrompts found:")
        for p in prompts:
            analyst = p.get("analyst", "unknown")
            content_len = len(p.get("content", ""))
            print(f"  - {analyst}: {content_len} chars")
    else:
        print("\nNo prompts found!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
