#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试新的分析任务，验证prompts修复"""

import sys
import json
import requests
import time

BASE_URL = "http://localhost:8000"
STOCK_CODE = "300033"

def main():
    print("=" * 60)
    print("Testing Prompts Fix: 300033 + deepseek")
    print("=" * 60)
    
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"username": "admin", "password": "admin123"}, timeout=30)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return 1
    token = resp.json()["data"]["access_token"]
    print(f"[OK] Login successful")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Start analysis
    payload = {
        "symbol": STOCK_CODE,
        "stock_code": STOCK_CODE,
        "parameters": {
            "market_type": "A股",
            "analysis_date": "2026-02-11",
            "research_depth": "快速",
            "selected_analysts": ["market", "fundamentals"],
            "include_sentiment": True,
            "include_risk": True,
            "language": "zh-CN",
            "quick_analysis_model": "deepseek-v3.2-exp-thinking",
            "deep_analysis_model": "deepseek-v3.2-exp-thinking",
            "analysis_level": 1
        }
    }
    
    print(f"\nStarting analysis:")
    print(f"  Stock: {STOCK_CODE}")
    print(f"  Model: deepseek-v3.2-exp-thinking")
    print(f"  Depth: 1 (fast)")
    print(f"  Analysts: market + fundamentals")
    
    resp = requests.post(f"{BASE_URL}/api/analysis/single",
                        json=payload, headers=headers, timeout=30)
    
    if resp.status_code != 200:
        print(f"\nFailed to start: {resp.status_code}")
        print(resp.text)
        return 1
    
    task_id = resp.json()["data"]["task_id"]
    print(f"\n[OK] Task started: {task_id}")
    
    # Wait for completion
    print("\nWaiting for analysis...")
    for i in range(60):
        time.sleep(5)
        resp = requests.get(f"{BASE_URL}/api/analysis/tasks/{task_id}/status", 
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
        else:
            print(f"  Status query failed")
    
    # Check prompts
    print("\nChecking prompts endpoint...")
    resp = requests.get(f"{BASE_URL}/api/reports/{task_id}/prompts", headers=headers, timeout=10)
    
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
        print(f"{resp.text[:500]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
