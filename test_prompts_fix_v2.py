#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试修复后的原始prompts保存"""

import sys
import json
import requests
import time

BASE_URL = "http://localhost:8000"
STOCK_CODE = "300033"

def main():
    print("=" * 60)
    print("Testing Raw Prompts Saving (Fixed)")
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
    for i in range(120):
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
        result = resp.json()
        prompts_data = result.get("data", {})
        prompts = prompts_data.get("prompts", [])
        source = prompts_data.get("source", "unknown")
        
        print(f"\nPrompts Response:")
        print(f"  Success: {result.get('success')}")
        print(f"  Message: {result.get('message')}")
        print(f"  Source: {source}")
        print(f"  Prompts count: {len(prompts)}")
        
        if prompts:
            print(f"\n  Found {len(prompts)} prompts:")
            for p in prompts:
                analyst = p.get('analyst', 'unknown')
                content_preview = p.get('content', '')[:150]
                print(f"    [OK] {analyst}:")
                print(f"       {content_preview}...")
            return 0
        else:
            print(f"  [FAIL] No prompts found!")
            return 1
    else:
        print(f"Failed to get prompts: {resp.status_code}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
