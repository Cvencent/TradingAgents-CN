"""直接检查数据库中的prompts"""
import sys
sys.path.insert(0, 'd:/trade/TradingAgents-CN')

from app.core.database import get_mongo_db
import asyncio

async def check_task():
    db = get_mongo_db()
    
    # 查找最近完成的任务
    task = await db.analysis_tasks.find_one(
        {"stock_symbol": "300033"},
        sort=[("created_at", -1)]
    )
    
    if not task:
        print("没有找到任务")
        return
    
    print(f"任务ID: {task.get('task_id')}")
    print(f"状态: {task.get('status')}")
    
    # 检查结果中的prompts
    result = task.get('result', {})
    
    if 'prompts' in result:
        prompts = result['prompts']
        print(f"\nPrompts数量: {len(prompts)}")
        for key, value in prompts.items():
            if isinstance(value, str):
                print(f"\n  {key}:")
                print(f"    长度: {len(value)}")
                print(f"    前200字符: {value[:200]}...")
    else:
        print("\n没有prompts字段")
    
    # 检查state中的原始prompt字段
    if 'state' in result:
        state = result['state']
        print(f"\n\nState中的prompt字段:")
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

asyncio.run(check_task())
