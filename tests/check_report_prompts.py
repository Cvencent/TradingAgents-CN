"""检查报告prompts"""
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

# 使用已完成的任务ID
task_id = "fb95922a-c9e8-4c70-a607-3b2b5e3a82b3"

print(f"获取报告 {task_id} 的prompts...\n")

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
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        prompts = data.get("data", {}).get("prompts", [])
        warning = data.get("data", {}).get("warning", "")
        
        print(f"\n{'='*60}")
        print(f"📊 结果汇总:")
        print(f"  - Prompts数量: {len(prompts)}")
        print(f"  - 警告: {warning or '无'}")
        print(f"{'='*60}")
        
        if prompts:
            print("\n📋 Prompts详情:")
            for i, p in enumerate(prompts):
                content = p.get('content', '')
                analyst = p.get('analyst', 'unknown')
                # 判断是否为原始prompt
                is_extracted = content.startswith('[从messages提取]') or content.startswith('[从report提取]')
                is_original = not is_extracted
                status = "✅ 原始" if is_original else "⚠️ 提取"
                print(f"\n  {i+1}. {analyst}: {len(content)} 字符 [{status}]")
                # 显示前500字符
                preview = content[:500].replace('\n', ' ')
                print(f"     预览: {preview}...")
    else:
        print(f"错误: {resp.text[:500]}")
except Exception as e:
    print(f"异常: {e}")
    import traceback
    traceback.print_exc()
