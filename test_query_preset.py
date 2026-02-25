"""
测试字符串查询预设
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def test_query():
    print("=== 测试字符串查询预设 ===")
    
    mongo_uri = "mongodb://admin:cwq297297@47.111.20.147:27117/"
    db_name = "tradingagents"
    
    client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    collection = db.model_selection_presets
    
    test_id = "699c405c1f7b1464e1b42e36"
    
    # 使用 ObjectId 查询
    print(f"\n1. 使用 ObjectId('{test_id}') 查询:")
    doc = await collection.find_one({"_id": ObjectId(test_id)})
    print(f"   结果: {doc}")
    
    # 使用字符串查询
    print(f"\n2. 使用字符串 '{test_id}' 查询:")
    doc = await collection.find_one({"_id": test_id})
    print(f"   结果: {doc}")
    
    # 查看一个文档的 _id 类型
    print("\n3. 查看现有文档的 _id 类型:")
    doc = await collection.find_one({})
    if doc:
        print(f"   _id: {doc.get('_id')}")
        print(f"   _id type: {type(doc.get('_id'))}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_query())
