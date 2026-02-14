#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查报告详情"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def main():
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"username": "admin", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    task_id = "651b584b-bcdf-4586-9178-c0f26f75977d"
    
    # Check the report detail
    resp = requests.get(f"{BASE_URL}/api/reports/{task_id}/detail", headers=headers)
    data = resp.json()["data"]
    
    print("Report detail keys:", list(data.keys()))
    
    if "prompts" in data:
        prompts = data["prompts"]
        print(f"\nPrompts in report: {len(prompts)} keys")
        for k in prompts.keys():
            print(f"  - {k}")
    else:
        print("\nNo prompts field in report")
    
    if "messages" in data:
        messages = data["messages"]
        print(f"\nMessages count: {len(messages)}")
        if messages:
            print(f"First message type: {messages[0].get('type', 'unknown')}")
            print(f"Last message type: {messages[-1].get('type', 'unknown')}")
    else:
        print("\nNo messages field in report")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
