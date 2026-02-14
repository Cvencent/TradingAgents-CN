"""测试 prompt 提取功能"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# 1. 登录获取 token
print("=" * 60)
print("[1/4] 登录获取 token...")
login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "admin",
    "password": "admin123"
})

if login_resp.status_code != 200:
    print(f"登录失败: {login_resp.status_code}")
    print(login_resp.text)
    exit(1)

token = login_resp.json()["data"]["access_token"]
print(f"✅ 登录成功，获取到 token")

headers = {"Authorization": f"Bearer {token}"}

# 2. 提交分析任务
print("\n" + "=" * 60)
print("[2/4] 提交分析任务...")
analysis_data = {
    "symbol": "300033",
    "stock_code": "300033",
    "parameters": {
        "market_type": "A股",
        "analysis_date": "2026-02-11",
        "research_depth": "快速",
        "selected_analysts": ["market", "fundamentals"],
        "include_sentiment": True,
        "include_risk": True,
        "language": "zh-CN",
        "quick_analysis_model": "deepseek-v3.2-exp-thinking",
        "deep_analysis_model": "deepseek-v3.2-exp-thinking",
        "analysis_level": 1
    }
}

submit_resp = requests.post(
    f"{BASE_URL}/api/analysis/single",
    json=analysis_data,
    headers=headers
)

if submit_resp.status_code != 200:
    print(f"提交分析任务失败: {submit_resp.status_code}")
    print(submit_resp.text)
    exit(1)

task_id = submit_resp.json()["data"]["task_id"]
print(f"✅ 分析任务已提交: {task_id}")

# 3. 等待分析完成
print("\n" + "=" * 60)
print("[3/4] 等待分析完成...")
max_wait = 300  # 最多等待5分钟
waited = 0

while waited < max_wait:
    status_resp = requests.get(
        f"{BASE_URL}/api/analysis/tasks/{task_id}/status",
        headers=headers
    )

    if status_resp.status_code == 200:
        status_data = status_resp.json()
        status = status_data.get("data", {}).get("status", "unknown")
        progress = status_data.get("data", {}).get("progress", 0)
        current_step = status_data.get("data", {}).get("current_step", "")

        print(f"  状态: {status}, 进度: {progress}%, 当前步骤: {current_step}")

        if status == "completed":
            print(f"✅ 分析完成！")
            break
        elif status == "failed":
            print(f"❌ 分析失败")
            exit(1)
    else:
        print(f"  查询状态失败: {status_resp.status_code}")

    time.sleep(5)
    waited += 5

if waited >= max_wait:
    print("❌ 等待超时")
    exit(1)

# 4. 获取报告 prompts
print("\n" + "=" * 60)
print("[4/4] 获取报告 prompts...")

# 首先获取任务详情
task_resp = requests.get(
    f"{BASE_URL}/api/analysis/tasks/{task_id}",
    headers=headers
)

if task_resp.status_code != 200:
    print(f"获取任务详情失败: {task_resp.status_code}")
    exit(1)

task_data = task_resp.json()
result = task_data.get("data", {}).get("result", {})
reports = result.get("reports", {})

print(f"\n报告列表:")
for key in reports.keys():
    print(f"  - {key}")

# 获取 prompts
prompts_resp = requests.get(
    f"{BASE_URL}/api/reports/{task_id}/prompts",
    headers=headers
)

if prompts_resp.status_code != 200:
    print(f"获取 prompts 失败: {prompts_resp.status_code}")
    print(prompts_resp.text)
    exit(1)

prompts_data = prompts_resp.json()
prompts = prompts_data.get("data", {}).get("prompts", [])

print(f"\n获取到 {len(prompts)} 个 prompts:")
for prompt in prompts:
    analyst = prompt.get("analyst", "unknown")
    content = prompt.get("content", "")
    print(f"\n  [{analyst}]")
    print(f"  内容长度: {len(content)}")
    if content:
        print(f"  内容预览: {content[:100]}...")

print("\n" + "=" * 60)
print("测试完成!")
