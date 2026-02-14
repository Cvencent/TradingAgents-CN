"""测试 prompts API"""
import requests
import json

BASE_URL = "http://localhost:8001"

# 登录获取token
def login():
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get("data", {}).get("access_token")
    return None

token = login()
if not token:
    print("登录失败")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 使用已完成的任务ID
task_id = "fb95922a-c9e8-4c70-a607-3b2b5e3a82b3"

print(f"测试报告 {task_id} 的 prompts API...\n")

try:
    resp = requests.get(
        f"{BASE_URL}/api/reports/{task_id}/prompts",
        headers=headers,
        timeout=10
    )
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n完整响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        prompts = data.get("data", {}).get("prompts", [])
        warning = data.get("data", {}).get("warning", "")
        source = data.get("data", {}).get("source", "")
        
        print(f"\n{'='*60}")
        print(f"📊 结果汇总:")
        print(f"  - Prompts数量: {len(prompts)}")
        print(f"  - 数据来源: {source}")
        print(f"  - 警告: {warning or '无'}")
        print(f"{'='*60}")
        
        # 检查每个prompt的内容
        for p in prompts:
            content = p.get("content", "")
            analyst = p.get("analyst", "")
            if "注：该任务未保存原始prompt" in content:
                print(f"\n❌ {analyst}: 显示的是提取的报告内容，不是原始prompt")
            else:
                print(f"\n✅ {analyst}: 显示的是原始prompt (前100字符: {content[:100]}...)")
    else:
        print(f"错误: {resp.text[:500]}")
except Exception as e:
    print(f"异常: {e}")
    import traceback
    traceback.print_exc()
