"""列出任务"""
import requests

BASE_URL = "http://localhost:8001"

# 登录获取token
def login():
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("access_token")
    return None

token = login()
if not token:
    print("登录失败")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 尝试不同的接口路径
endpoints = [
    "/api/analysis/tasks",
    "/api/tasks",
    "/api/analysis/list",
]

for endpoint in endpoints:
    try:
        resp = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            timeout=10
        )
        print(f"{endpoint}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  响应: {resp.json()}")
    except Exception as e:
        print(f"{endpoint}: 异常 - {e}")
    print()
