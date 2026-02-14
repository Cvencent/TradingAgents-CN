"""检查数据库中文档的结构"""
from pymongo import MongoClient

# 连接MongoDB（使用远程服务器）
mongo_uri = "mongodb://admin:cwq297297@47.111.20.147:27117/tradingagents?authSource=admin"
client = MongoClient(mongo_uri)
db = client.get_database()

# 查找最近完成的分析任务
task = db.analysis_tasks.find_one(
    {"stock_symbol": "300033", "status": "completed"},
    sort=[("created_at", -1)]
)

if not task:
    print("没有找到已完成的分析任务")
    exit(1)

print(f"任务ID: {task.get('task_id')}")
print(f"状态: {task.get('status')}")
print(f"股票代码: {task.get('stock_symbol')}")

result = task.get('result', {})
print(f"\n结果字段: {list(result.keys())}")

# 检查prompts字段
if 'prompts' in result:
    prompts = result['prompts']
    print(f"\n✅ prompts字段存在，包含 {len(prompts)} 个prompts")
    for key in prompts.keys():
        print(f"  - {key}")
else:
    print("\n❌ prompts字段不存在")

# 检查state字段
if 'state' in result:
    state = result['state']
    print(f"\nstate字段存在，包含以下字段:")
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
    
    # 检查保存的request_prompt字段
    print(f"\n检查保存的request_prompt字段:")
    prompt_fields = [
        'market_request_prompt',
        'fundamentals_prompt',
        'sentiment_request_prompt',
        'news_request_prompt',
        'capital_flow_request_prompt'
    ]
    for field in prompt_fields:
        if field in state:
            value = state[field]
            if isinstance(value, str):
                print(f"  ✅ {field}: 存在, 长度 {len(value)}")
            else:
                print(f"  ⚠️ {field}: 存在但类型为 {type(value)}")
        else:
            print(f"  ❌ {field}: 不存在")
else:
    print("\n❌ state字段不存在")

# 检查analysis_reports集合
print(f"\n\n检查analysis_reports集合:")
report = db.analysis_reports.find_one(
    {"task_id": task.get('task_id')}
)

if report:
    print(f"✅ 找到对应的分析报告")
    print(f"报告字段: {list(report.keys())}")
    
    if 'prompts' in report:
        prompts = report['prompts']
        print(f"\n✅ analysis_reports中的prompts字段存在，包含 {len(prompts)} 个prompts")
        for key in prompts.keys():
            print(f"  - {key}")
    else:
        print("\n❌ analysis_reports中的prompts字段不存在")
else:
    print("❌ 未找到对应的分析报告")

client.close()
