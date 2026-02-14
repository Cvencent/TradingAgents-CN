import requests, json, sys

r = requests.post('http://localhost:8000/api/auth/login', json={'username':'admin','password':'admin123'})
token = r.json()['data']['access_token']

# 获取完整任务详情
r2 = requests.get('http://localhost:8000/api/analysis/tasks/007bc602-771d-4b02-8d57-40d8dace38c2/details', headers={'Authorization':f'Bearer {token}'})

data = r2.json()
if data.get("success"):
    details = data.get("data", {})
    # 保存完整JSON
    with open('D:/trade/TradingAgents-CN/task_details.json', 'w', encoding='utf-8') as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print("Details saved to task_details.json")
    
    # 打印关键信息
    print("\n=== KEY INFO ===")
    print("Status:", details.get("status"))
    print("Current step:", details.get("current_step"))
    print("Error message:", details.get("error_message", "No error")[:500])
    
    # 查找失败步骤
    steps = details.get("steps", [])
    for step in steps:
        if step.get("status") == "failed":
            print(f"\nFailed step: {step.get('name')}")
            print(f"Description: {step.get('description')}")
else:
    print("Failed to get details:", data)
