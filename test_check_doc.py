"""
检查 MongoDB 中预设的实际文档结构
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_preset_doc():
    print("=== 检查预设文档结构 ===")
    
    mongo_uri = "mongodb://admin:cwq297297@47.111.20.147:27117/"
    db_name = "tradingagents"
    
    try:
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        collection = db.model_selection_presets
        
        # 获取一个文档
        doc = await collection.find_one({})
        if doc:
            print(f"文档 keys: {doc.keys()}")
            print(f"\n完整文档:")
            for key, value in doc.items():
                if key == 'role_configs':
                    print(f"  {key}: {value}")
                    print(f"    type: {type(value)}")
                    if isinstance(value, dict):
                        for k, v in value.items():
                            print(f"      {k}: {v} (type: {type(v)})")
                else:
                    print(f"  {key}: {value} (type: {type(value)})")
        
        client.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_preset_doc())
