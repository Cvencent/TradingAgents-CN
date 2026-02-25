"""
简化API测试
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_get_role_configs():
    """测试获取角色配置"""
    print("\n=== 测试获取角色配置 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/config/role-models")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        if data.get('success') and data.get('data'):
            role_data = data['data']
            print(f"分析师: {len(role_data.get('analysts', []))}")
            print(f"辩论者: {len(role_data.get('debaters', []))}")
            print(f"决策者: {len(role_data.get('decision_makers', []))}")
        return data.get('success', False)

async def test_get_presets():
    """测试获取预设列表"""
    print("\n=== 测试获取预设列表 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/config/model-presets")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            if data.get('success'):
                presets = data.get('data', [])
                print(f"预设数量: {len(presets)}")
                return True
            else:
                print(f"Message: {data.get('message')}")
        else:
            print(f"错误: {response.text[:200]}")
        return False

async def test_batch_update():
    """测试批量更新"""
    print("\n=== 测试批量更新 ===")
    async with httpx.AsyncClient() as client:
        # 注意：FastAPI 期望的请求格式
        batch_data = {
            "configs": [
                {
                    "role_id": "market",
                    "provider": "openai",
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "timeout": 180,
                    "is_enabled": True
                }
            ]
        }
        response = await client.put(
            f"{BASE_URL}/api/config/role-models/batch",
            json=batch_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            return data.get('success', False)
        else:
            print(f"错误: {response.text[:500]}")
            return False

async def main():
    print("=" * 60)
    print("简化API测试")
    print("=" * 60)
    
    results = []
    results.append(("获取角色配置", await test_get_role_configs()))
    results.append(("获取预设列表", await test_get_presets()))
    results.append(("批量更新", await test_batch_update()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    print(f"\n总计: {passed}/{len(results)} 通过")

if __name__ == "__main__":
    asyncio.run(main())
