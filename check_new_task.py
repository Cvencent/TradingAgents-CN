#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查新任务的状态和prompts"""

import sys
import requests
import time

BASE_URL = "http://localhost:8000"
TASK_ID = "a5cc5b31-0148-48dd-a37d-5719c8a2cddc"

def main():
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"username": "admin", "password": "admin123"}, timeout=30)
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Checking task: {TASK_ID}")
    
    # Wait for completion
    print("\nWaiting for analysis...")
    for i in range(60):
        time.sleep(5)
        resp = requests.get(f"{BASE_URL}/api/analysis/tasks/{TASK_ID}/status", 
                           headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()["data"]
            status = data["status"]
            progress = data.get("progress", 0)
            print(f"  [{i*5+5}s] {status} ({progress}%)")
            
            if status == "completed":
                print("\n[OK] Analysis completed!")
                break
            elif status == "failed":
                error = data.get("error_message", "Unknown error")
                print(f"\n[FAIL] Analysis failed: {error}")
                return 1
    
    # Check prompts
    print("\nChecking prompts...")
    resp = requests.get(f"{BASE_URL}/api/reports/{TASK_ID}/prompts", headers=headers, timeout=10)
    
    if resp.status_code == 200:
        prompts_data = resp.json()["data"]
        prompts = prompts_data.get("prompts", [])
        prompts_by_step = prompts_data.get("prompts_by_step", {})
        warning = prompts_data.get("warning", "")
        
        print(f"\nPrompts Response:")
        print(f"  Prompts count: {len(prompts)}")
        print(f"  Prompts by step count: {len(prompts_by_step)}")
        if warning:
            print(f"  Warning: {warning}")
        
        if prompts:
            print(f"\n  Found {len(prompts)} prompts:")
            for p in prompts:
                analyst = p.get('analyst', 'unknown')
                content_len = len(p.get('content', ''))
                print(f"    [OK] {analyst}: {content_len} chars")
            return 0
        else:
            print(f"  [FAIL] No prompts found!")
            return 1
    else:
        print(f"Failed to get prompts: {resp.status_code}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
