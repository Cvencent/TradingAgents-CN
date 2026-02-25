"""
测试简单端点
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_health():
    """测试健康检查端点"""
    print("\n=== 测试健康检查端点 ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
        except Exception as e:
            print(f"错误: {e}")

async def test_test_log():
    """测试日志端点"""
    print("\n=== 测试日志端点 ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/test-log", timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
        except Exception as e:
            print(f"错误: {e}")

async def test_role_models():
    """测试角色配置端点"""
    print("\n=== 测试角色配置端点 ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/config/role-models", timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:500]}")
        except Exception as e:
            print(f"错误: {e}")

async def main():
    print("=" * 60)
    print("简单端点测试")
    print("=" * 60)
    
    await test_health()
    await test_test_log()
    await test_role_models()

if __name__ == "__main__":
    asyncio.run(main())
