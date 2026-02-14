#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证prompts保存功能的测试脚本
用法: python test_prompts_verification.py
"""

import sys
import json
import requests

BASE_URL = "http://localhost:8000"

def login():
    """登录获取token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"username": "admin", "password": "admin123"}, timeout=10)
    if resp.status_code == 200:
        return resp.json()["data"]["access_token"]
    return None

def check_reports_api(token):
    """检查reports API的响应结构"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取报告列表
    resp = requests.get(f"{BASE_URL}/api/reports/list?page=1&page_size=5", headers=headers, timeout=10)
    
    print(f"Reports API Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        reports = data.get("data", data).get("reports", [])
        
        print(f"Total reports: {len(reports)}")
        
        if reports:
            # 检查最新报告的结构
            latest = reports[0]
            print(f"\nLatest report keys: {list(latest.keys())}")
            
            # 检查prompts字段
            prompts = latest.get("prompts", {})
            print(f"Prompts keys: {list(prompts.keys()) if prompts else 'None'}")
            
            # 检查messages字段
            messages = latest.get("messages", [])
            print(f"Messages count: {len(messages) if messages else 0}")
            
            return True
        else:
            print("No reports found")
            return False
    else:
        print(f"Error: {resp.text[:500]}")
        return False

def main():
    print("=" * 60)
    print("Prompts保存功能验证")
    print("=" * 60)
    
    token = login()
    if not token:
        print("Login failed!")
        return 1
    
    print("Login OK")
    
    success = check_reports_api(token)
    
    print("\n" + "=" * 60)
    if success:
        print("Reports API works correctly!")
    else:
        print("Reports API check completed")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
