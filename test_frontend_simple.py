"""
前端页面功能测试 - 简化版
测试基本功能是否可用
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_page_load():
    """测试页面加载所需的基础API"""
    print("\n=== 测试页面加载 ===")
    
    async with httpx.AsyncClient() as client:
        # 测试1: 获取厂家列表（页面加载必需）
        print("\n1. 获取厂家列表...")
        try:
            response = await client.get(f"{BASE_URL}/api/config/llm/providers", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"   ✅ 成功: {len(data)} 个厂家")
                    return True
                else:
                    print(f"   ❌ 响应格式错误")
            else:
                print(f"   ❌ 状态码: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        return False

async def test_role_config_apis():
    """测试角色配置相关API"""
    print("\n=== 测试角色配置API ===")
    
    async with httpx.AsyncClient() as client:
        # 测试1: 获取角色配置
        print("\n1. 获取角色配置...")
        try:
            response = await client.get(f"{BASE_URL}/api/config/role-models", timeout=10)
            print(f"   状态码: {response.status_code}")
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            if data.get('success') and data.get('data'):
                role_data = data['data']
                print(f"   ✅ 成功")
                print(f"      - 分析师: {len(role_data.get('analysts', []))}")
                print(f"      - 辩论者: {len(role_data.get('debaters', []))}")
                print(f"      - 决策者: {len(role_data.get('decision_makers', []))}")
                return True
            else:
                print(f"   ❌ 失败: {data.get('message')}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
        return False

async def test_preset_apis():
    """测试预设相关API"""
    print("\n=== 测试预设API ===")
    
    async with httpx.AsyncClient() as client:
        # 测试1: 获取预设列表
        print("\n1. 获取预设列表...")
        try:
            response = await client.get(f"{BASE_URL}/api/config/model-presets", timeout=10)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                if data.get('success'):
                    presets = data.get('data', [])
                    print(f"   ✅ 成功: {len(presets)} 个预设")
                    return True
                else:
                    print(f"   Message: {data.get('message')}")
            else:
                print(f"   错误: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
        return False

async def main():
    print("=" * 60)
    print("角色模型配置功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试页面加载
    results.append(("页面加载", await test_page_load()))
    
    # 测试角色配置
    results.append(("角色配置API", await test_role_config_apis()))
    
    # 测试预设
    results.append(("预设API", await test_preset_apis()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！功能基本可用。")
    else:
        print("\n⚠️ 部分测试失败，需要修复。")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
