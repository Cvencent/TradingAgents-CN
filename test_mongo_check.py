"""
检查 MongoDB 集合
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check_mongo():
    """检查 MongoDB 集合"""
    print("=== 检查 MongoDB 集合 ===")
    
    # 使用正确的连接字符串
    mongo_uri = "mongodb://admin:cwq297297@47.111.20.147:27117/"
    db_name = "tradingagents"
    
    print(f"连接: {mongo_uri}")
    print(f"数据库: {db_name}")
    
    try:
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # 检查集合列表
        collections = await db.list_collection_names()
        print(f"\n✅ 连接成功")
        print(f"集合列表: {collections}")
        
        # 检查 role_model_configs 集合
        if "role_model_configs" in collections:
            print(f"\n✅ role_model_configs 集合存在")
            count = await db.role_model_configs.count_documents({})
            print(f"   文档数量: {count}")
            
            # 查看前几个文档
            print("\n   前3个文档:")
            async for doc in db.role_model_configs.find().limit(3):
                print(f"     - {doc.get('role_id', 'N/A')}: {doc.get('provider', 'N/A')}/{doc.get('model_name', 'N/A')}")
        else:
            print(f"\n⚠️ role_model_configs 集合不存在，将创建")
        
        # 检查 model_selection_presets 集合
        if "model_selection_presets" in collections:
            print(f"\n✅ model_selection_presets 集合存在")
            count = await db.model_selection_presets.count_documents({})
            print(f"   文档数量: {count}")
        else:
            print(f"\n⚠️ model_selection_presets 集合不存在，将创建")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_mongo())
