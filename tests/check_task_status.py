"""检查任务状态"""
import requests
import time

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

# 任务ID - 使用刚才创建的任务
task_id = "fb95922a-c9e8-4c70-a607-3b2b5e3a82b3"

print(f"查询任务 {task_id} 的状态...\n")

for i in range(60):
    try:
        resp = requests.get(
            f"{BASE_URL}/api/analysis/tasks/{task_id}/status",
            headers=headers,
            timeout=10
        )
        print(f"[{i}] 状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    响应: {data}")
            status = data.get("status")
            progress = data.get("progress", 0)
            print(f"    状态: {status} | 进度: {progress}%")
            
            if status == "completed":
                print("\n✅ 分析完成!")
                break
            elif status == "failed":
                print(f"\n❌ 分析失败: {data.get('error')}")
                break
        else:
            print(f"    错误: {resp.text[:200]}")
    except Exception as e:
        print(f"    异常: {e}")
    
    time.sleep(5)
    print()
