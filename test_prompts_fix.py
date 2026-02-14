#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试prompts修复"""

import sys
import requests

BASE_URL = "http://localhost:8000"
TASK_ID = "a5cc5b31-0148-48dd-a37d-5719c8a2cddc"

def main():
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"username": "admin", "password": "admin123"}, timeout=30)
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing prompts for task: {TASK_ID}")
    
    # Check prompts
    print("\nChecking prompts endpoint...")
    resp = requests.get(f"{BASE_URL}/api/reports/{TASK_ID}/prompts", headers=headers, timeout=10)
    
    if resp.status_code == 200:
        result = resp.json()
        prompts_data = result.get("data", {})
        prompts = prompts_data.get("prompts", [])
        prompts_by_step = prompts_data.get("prompts_by_step", {})
        warning = prompts_data.get("warning", "")
        source = prompts_data.get("source", "unknown")
        
        print(f"\nPrompts Response:")
        print(f"  Success: {result.get('success')}")
        print(f"  Message: {result.get('message')}")
        print(f"  Source: {source}")
        print(f"  Prompts count: {len(prompts)}")
        print(f"  Prompts by step count: {len(prompts_by_step)}")
        if warning:
            print(f"  Warning: {warning}")
        
        if prompts:
            print(f"\n  Found {len(prompts)} prompts:")
            for p in prompts:
                analyst = p.get('analyst', 'unknown')
                analyst_name = p.get('analyst_name', 'unknown')
                content = p.get('content', '')
                content_preview = content[:100] + "..." if len(content) > 100 else content
                print(f"    [OK] {analyst_name} ({analyst}): {len(content)} chars")
                print(f"       Preview: {content_preview}")
            return 0
        else:
            print(f"  [FAIL] No prompts found!")
            return 1
    else:
        print(f"Failed to get prompts: {resp.status_code}")
        print(f"{resp.text[:500]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
