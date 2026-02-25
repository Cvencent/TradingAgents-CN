"""
测试预设API
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_get_presets():
    """测试获取预设列表"""
    print("\n=== 测试获取预设列表 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/config/model-presets")
        print(f"状态码: {response.status_code}")
        try:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
        except Exception as e:
            print(f"解析错误: {e}")
            print(f"原始响应: {response.text[:500]}")

async def test_create_preset():
    """测试创建预设 - 带必需字段"""
    print("\n=== 测试创建预设（带必需字段）===")
    async with httpx.AsyncClient() as client:
        preset_data = {
            "name": "测试预设",
            "description": "用于测试的预设",
            "preset_type": "user",
            "is_active": True,
            "default_provider": "openai",
            "default_model": "gpt-4",
            "role_configs": {
                "market": {
                    "provider": "openai",
                    "model_name": "gpt-4",
                    "temperature": 0.8
                }
            }
        }
        response = await client.post(
            f"{BASE_URL}/api/config/model-presets",
            json=preset_data
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

async def test_batch_update():
    """测试批量更新 - 正确格式"""
    print("\n=== 测试批量更新（正确格式）===")
    async with httpx.AsyncClient() as client:
        batch_data = {
            "configs": [
                {
                    "role_id": "market",
                    "provider": "openai",
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "is_enabled": True
                },
                {
                    "role_id": "bull",
                    "provider": "openai",
                    "model_name": "gpt-3.5-turbo",
                    "temperature": 0.5,
                    "is_enabled": True
                }
            ]
        }
        response = await client.put(
            f"{BASE_URL}/api/config/role-models/batch",
            json=batch_data
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

async def main():
    print("=" * 60)
    print("测试预设API")
    print("=" * 60)
    
    await test_get_presets()
    await test_create_preset()
    await test_batch_update()

if __name__ == "__main__":
    asyncio.run(main())
