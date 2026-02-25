"""测试多个端点"""
import requests
import json

endpoints = [
    'http://127.0.0.1:8001/api/test-log',
    'http://127.0.0.1:8001/api/test-role-config',
    'http://127.0.0.1:8001/api/config/model-selection/active',
]

for url in endpoints:
    print(f"\n{'='*60}")
    print(f"GET {url}")
    print('='*60)
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"Error: {e}")
