"""
检查 MongoDB 中的预设结构
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_presets():
    print("=== 检查预设集合 ===")
    
    mongo_uri = "mongodb://admin:cwq297297@47.111.20.147:27117/"
    db_name = "tradingagents"
    
    try:
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # 检查 model_selection_presets 集合
        collection = db.model_selection_presets
        count = await collection.count_documents({})
        print(f"预设文档数: {count}")
        
        if count > 0:
            print("\n预设列表:")
            async for doc in collection.find():
                print(f"  - {doc.get('name')}: {doc.keys()}")
        
        client.close()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_presets())
