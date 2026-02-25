"""
直接调试服务方法
"""
import asyncio
import sys
import traceback
import os

# 设置环境变量
os.environ["MONGODB_CONNECTION_STRING"] = "mongodb://admin:cwq297297@47.111.20.147:27117/"
os.environ["MONGODB_DATABASE_NAME"] = "tradingagents"
os.environ["USE_MONGODB_STORAGE"] = "true"

# 设置日志
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_service():
    """直接测试服务方法"""
    print("=== 直接测试服务方法 ===\n")
    
    try:
        print("1. 初始化数据库连接...")
        from app.core.database import init_database, get_mongo_db
        await init_database()
        print("   ✅ 数据库初始化成功")
        
        print("\n2. 导入服务类...")
        from app.services.role_model_config_service import RoleModelConfigService
        print("   ✅ 导入成功")
        
        print("\n3. 创建服务实例...")
        service = RoleModelConfigService()
        print("   ✅ 创建成功")
        
        print("\n4. 测试 _get_db 方法...")
        db = await service._get_db()
        print(f"   ✅ 获取数据库成功")
        
        print("\n5. 测试集合访问...")
        collection = db.role_model_configs
        count = await collection.count_documents({})
        print(f"   ✅ 集合访问成功，文档数: {count}")
        
        print("\n6. 调用 get_all_role_configs...")
        result = await service.get_all_role_configs()
        print(f"   ✅ 成功!")
        print(f"      - 分析师: {len(result.get('analysts', []))}")
        print(f"      - 辩论者: {len(result.get('debaters', []))}")
        print(f"      - 决策者: {len(result.get('decision_makers', []))}")
        
        print("\n7. 测试 get_all_presets...")
        presets = await service.get_all_presets()
        print(f"   ✅ 成功! 预设数: {len(presets)}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print(f"错误类型: {type(e)}")
        print(f"\n完整堆栈:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_service())
    sys.exit(0 if success else 1)
