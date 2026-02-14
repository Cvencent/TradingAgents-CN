"""等待服务就绪"""
import requests
import time

BASE_URL = "http://localhost:8001"

print("⏳ 等待后端服务就绪...")
for i in range(120):
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if resp.status_code == 200:
            print(f"✅ 服务已就绪! (等待了 {i} 秒)")
            exit(0)
    except:
        pass
    if i % 10 == 0:
        print(f"  还在等待... ({i}秒)")
    time.sleep(1)

print("❌ 等待超时")
exit(1)
