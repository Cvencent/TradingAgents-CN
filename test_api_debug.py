#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""直接测试API的prompts提取"""

import requests
import json

BASE_URL = "http://localhost:8000"
TASK_ID = "a5cc5b31-0148-48dd-a37d-5719c8a2cddc"

def main():
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"username": "admin", "password": "admin123"}, timeout=30)
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 直接调用API
    resp = requests.get(f"{BASE_URL}/api/reports/{TASK_ID}/prompts", headers=headers, timeout=10)
    result = resp.json()
    
    print("API Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
