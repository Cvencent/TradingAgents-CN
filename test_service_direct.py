"""直接测试服务方法"""
import asyncio
import sys
sys.path.insert(0, 'd:\\trade\\TradingAgents-CN')

async def test_get_active_config():
    from app.services.role_model_config_service import RoleModelConfigService
    
    service = RoleModelConfigService()
    try:
        print("开始调用 get_active_config...")
        result = await service.get_active_config()
        print(f"成功! 结果: {result}")
        return result
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        print(f"堆栈: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    asyncio.run(test_get_active_config())
