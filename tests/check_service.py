"""检查服务是否就绪"""
import requests
import sys

BASE_URL = "http://localhost:8000"
HEADERS = {
    "Authorization": "Bearer test_token",
    "Content-Type": "application/json"
}

def check():
    try:
        resp = requests.get(f"{BASE_URL}/api/health", headers=HEADERS, timeout=5)
        print(f"Health check: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ 服务已就绪!")
            return True
    except Exception as e:
        print(f"❌ 服务未就绪: {e}")
    return False

if __name__ == "__main__":
    if check():
        sys.exit(0)
    else:
        sys.exit(1)
