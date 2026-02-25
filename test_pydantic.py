"""
直接测试 Pydantic 模型解析 - 使用真实的 MongoDB ObjectId
"""
import asyncio
import sys
sys.path.insert(0, 'd:/trade/TradingAgents-CN')

async def test_model():
    print("=== 测试 Pydantic 模型解析 ===")
    
    from app.models.role_model_config import ModelSelectionPreset
    from datetime import datetime
    from bson import ObjectId
    
    # 模拟 MongoDB 文档 - 使用有效的 ObjectId
    doc = {
        "_id": ObjectId(),
        "name": "测试预设",
        "description": "测试描述",
        "preset_type": "user",
        "role_configs": {
            "analyst_market": {
                "provider": "openai",
                "model_name": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 4000
            }
        },
        "default_provider": "openai",
        "default_model": "gpt-4o",
        "is_active": True,
        "is_system": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "created_by": "admin"
    }
    
    try:
        preset = ModelSelectionPreset(**doc)
        print(f"✅ 解析成功!")
        print(f"  id: {preset.id}")
        print(f"  name: {preset.name}")
        
        # 测试 model_dump
        dump = preset.model_dump()
        print(f"  model_dump: {dump}")
        
        dump_by_alias = preset.model_dump(by_alias=True)
        print(f"  model_dump(by_alias=True): {dump_by_alias}")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_model())
