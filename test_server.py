import requests
import time

for i in range(10):
    try:
        print(f"尝试 {i+1}/10...")
        r = requests.get('http://127.0.0.1:8000/api/health', timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)
