"""
测试 MongoDB 预设数据
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def test_mongo_presets():
    client = AsyncIOMotorClient(settings.MONGODB_CONNECTION_STRING)
    db = client[settings.MONGODB_DATABASE_NAME]
    
    print("=== 检查 model_selection_presets 集合 ===")
    
    # 检查集合是否存在
    collections = await db.list_collection_names()
    print(f"集合列表: {collections}")
    
    if "model_selection_presets" in collections:
        collection = db.model_selection_presets
        
        # 统计文档数量
        count = await collection.count_documents({})
        print(f"预设数量: {count}")
        
        # 查看前几个文档
        print("\n前3个文档:")
        async for doc in collection.find().limit(3):
            print(f"  - ID: {doc.get('_id')}")
            print(f"    Name: {doc.get('name')}")
            print(f"    Type: {doc.get('preset_type')}")
            print(f"    Default Provider: {doc.get('default_provider')}")
            print(f"    Default Model: {doc.get('default_model')}")
            print(f"    Role Configs: {doc.get('role_configs')}")
            print()
    else:
        print("集合不存在")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_mongo_presets())
