"""检查数据库中保存的prompts"""
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

print(f"获取任务 {task_id} 的完整数据...\n")

try:
    # 获取任务详情
    resp = requests.get(
        f"{BASE_URL}/api/analysis/tasks/{task_id}/details",
        headers=headers,
        timeout=10
    )
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        
        # 检查state中的字段
        if "data" in data and "state" in data["data"]:
            state = data["data"]["state"]
            print(f"\nState中的字段:")
            for key in state.keys():
                value = state[key]
                if isinstance(value, str):
                    print(f"  - {key}: 字符串, 长度 {len(value)}")
                elif isinstance(value, list):
                    print(f"  - {key}: 列表, 长度 {len(value)}")
                elif isinstance(value, dict):
                    print(f"  - {key}: 字典, 键 {list(value.keys())}")
                else:
                    print(f"  - {key}: {type(value)}")
            
            # 检查是否有保存的request_prompt字段
            prompt_fields = [
                'market_request_prompt',
                'fundamentals_prompt',
                'sentiment_request_prompt',
                'news_request_prompt',
                'capital_flow_request_prompt'
            ]
            
            print(f"\n\n检查保存的prompt字段:")
            for field in prompt_fields:
                if field in state:
                    value = state[field]
                    if isinstance(value, str):
                        print(f"  ✅ {field}: 存在, 长度 {len(value)}")
                        print(f"     前100字符: {value[:100]}...")
                    else:
                        print(f"  ⚠️ {field}: 存在但类型为 {type(value)}")
                else:
                    print(f"  ❌ {field}: 不存在")
        else:
            print("没有state数据")
            print(f"响应结构: {list(data.keys())}")
    else:
        print(f"错误: {resp.text[:500]}")
except Exception as e:
    print(f"异常: {e}")
    import traceback
    traceback.print_exc()
