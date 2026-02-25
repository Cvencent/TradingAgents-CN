"""
角色模型配置API测试脚本
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_get_role_configs():
    """测试获取所有角色配置"""
    print("\n=== 测试获取所有角色配置 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/config/role-models")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get("success"):
            print("✅ 获取角色配置成功")
            if "data" in data:
                role_data = data["data"]
                print(f"   - 分析师数量: {len(role_data.get('analysts', []))}")
                print(f"   - 辩论者数量: {len(role_data.get('debaters', []))}")
                print(f"   - 决策者数量: {len(role_data.get('decision_makers', []))}")
            return True
        else:
            print("❌ 获取角色配置失败")
            return False

async def test_get_providers():
    """测试获取厂家列表"""
    print("\n=== 测试获取厂家列表 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/config/llm/providers")
        print(f"状态码: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print("✅ 获取厂家列表成功")
            if isinstance(data, list):
                print(f"   - 厂家数量: {len(data)}")
                for provider in data[:3]:
                    print(f"   - {provider.get('display_name', provider.get('name'))}: {provider.get('is_active', False)}")
            return True
        else:
            print("❌ 获取厂家列表失败")
            return False

async def test_update_role_config():
    """测试更新角色配置"""
    print("\n=== 测试更新角色配置 ===")
    async with httpx.AsyncClient() as client:
        update_data = {
            "provider": "openai",
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 180,
            "is_enabled": True
        }
        response = await client.put(
            f"{BASE_URL}/api/config/role-models/market",
            json=update_data
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get("success"):
            print("✅ 更新角色配置成功")
            return True
        else:
            print("❌ 更新角色配置失败")
            return False

async def test_get_presets():
    """测试获取预设列表"""
    print("\n=== 测试获取预设列表 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/config/model-presets")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
        
        if response.status_code == 200 and data.get("success"):
            print("✅ 获取预设列表成功")
            presets = data.get("data", [])
            print(f"   - 预设数量: {len(presets)}")
            return True
        else:
            print("❌ 获取预设列表失败")
            return False

async def test_create_preset():
    """测试创建预设"""
    print("\n=== 测试创建预设 ===")
    async with httpx.AsyncClient() as client:
        preset_data = {
            "name": "测试预设",
            "description": "用于测试的预设",
            "preset_type": "user",
            "is_active": True,
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
        
        if response.status_code == 200 and data.get("success"):
            print("✅ 创建预设成功")
            return data.get("data", {}).get("id")
        else:
            print("❌ 创建预设失败")
            return None

async def test_delete_preset(preset_id: str):
    """测试删除预设"""
    print(f"\n=== 测试删除预设 {preset_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{BASE_URL}/api/config/model-presets/{preset_id}")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and data.get("success"):
            print("✅ 删除预设成功")
            return True
        else:
            print("❌ 删除预设失败")
            return False

async def test_batch_update():
    """测试批量更新"""
    print("\n=== 测试批量更新角色配置 ===")
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
        
        if response.status_code == 200 and data.get("success"):
            print("✅ 批量更新成功")
            return True
        else:
            print("❌ 批量更新失败")
            return False

async def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始角色模型配置API测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 获取角色配置
    results.append(("获取角色配置", await test_get_role_configs()))
    
    # 测试2: 获取厂家列表
    results.append(("获取厂家列表", await test_get_providers()))
    
    # 测试3: 更新角色配置
    results.append(("更新角色配置", await test_update_role_config()))
    
    # 测试4: 获取预设列表
    results.append(("获取预设列表", await test_get_presets()))
    
    # 测试5: 创建预设
    preset_id = await test_create_preset()
    results.append(("创建预设", preset_id is not None))
    
    # 测试6: 批量更新
    results.append(("批量更新", await test_batch_update()))
    
    # 测试7: 删除预设（如果创建成功）
    if preset_id:
        results.append(("删除预设", await test_delete_preset(preset_id)))
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    print(f"\n总计: {passed}/{total} 通过")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
