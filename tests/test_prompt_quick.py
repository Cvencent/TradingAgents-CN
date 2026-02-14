"""
快速测试：检查prompt提取功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 登录获取token
print("🔐 正在登录...")
resp = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": "admin", "password": "admin123"},
    timeout=10
)
if resp.status_code != 200:
    print(f"❌ 登录失败: {resp.text[:500]}")
    exit(1)

token = resp.json().get("data", {}).get("access_token")
print(f"✅ 登录成功!")

# 获取最近的报告ID
print("🔍 查找最近的A股单股分析报告...")
from pymongo import MongoClient
mongo_uri = "mongodb://admin:cwq297297@47.111.20.147:27117/tradingagents?authSource=admin"
client = MongoClient(mongo_uri)
db = client.get_database()

# 查找最近的已完成的任务
task = db.analysis_tasks.find_one(
    {"stock_symbol": "300033", "status": "completed"},
    sort=[("created_at", -1)]
)

if not task:
    print("❌ 未找到300033的分析任务")
    exit(1)

report_id = str(task.get("_id"))
print(f"✅ 找到报告ID: {report_id}")

# 调用prompt接口
print(f"🔍 调用 /api/reports/{report_id}/prompts 接口...")
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(f"{BASE_URL}/api/reports/{report_id}/prompts", headers=headers, timeout=10)

if resp.status_code != 200:
    print(f"❌ 接口调用失败: {resp.status_code} - {resp.text[:500]}")
    exit(1)

data = resp.json()
print(f"✅ 接口返回成功!")
print(f"   - 成功: {data.get('success')}")
print(f"   - 消息: {data.get('message')}")
print(f"   - prompt数量: {data.get('data', {}).get('count', 0)}")
print(f"   - 来源: {data.get('data', {}).get('source', 'unknown')}")

# 检查是否有原始prompt
prompts = data.get("data", {}).get("prompts", [])
if prompts:
    print(f"\n✅ 找到 {len(prompts)} 个prompts:")
    for p in prompts:
        content = p.get("content", "")
        if "注：该任务未保存原始prompt" in content:
            print(f"   ❌ {p.get('analyst')}: 包含 '[注：该任务未保存原始prompt...]'")
        else:
            print(f"   ✅ {p.get('analyst')}: 原始prompt (长度: {len(content)} 字符)")
else:
    print("\n❌ 未找到任何prompts")

print("\n测试完成!")
