"""使用 requests 测试 API"""
import requests
import json

try:
    response = requests.get('http://127.0.0.1:8001/api/config/model-selection/active', timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(traceback.format_exc())
