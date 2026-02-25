"""
测试创建预设 API - 正确格式
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_create_preset():
    print("\n=== 测试创建预设 ===")
    
    async with httpx.AsyncClient() as client:
        # 登录
        login_data = {"username": "admin", "password": "admin123"}
        response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=30)
        token = response.json().get("data", {}).get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建预设 - 使用正确格式的 role_configs
        preset_data = {
            "name": "测试预设2",
            "description": "测试描述",
            "role_configs": {
                "analyst_market": {
                    "provider": "openai",
                    "model_name": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            },
            "default_provider": "openai",
            "default_model": "gpt-4o"
        }
        
        print("\n创建预设...")
        response = await client.post(
            f"{BASE_URL}/api/config/model-presets", 
            json=preset_data, 
            headers=headers, 
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_create_preset())
