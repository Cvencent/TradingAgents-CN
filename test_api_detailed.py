"""
详细 API 测试
"""
import asyncio
import httpx
import json
import traceback

BASE_URL = "http://localhost:8000"

async def test_get_role_configs():
    """测试获取角色配置 - 详细版"""
    print("\n=== 测试获取角色配置 ===")
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"发送请求: GET {BASE_URL}/api/config/role-models")
            response = await client.get(
                f"{BASE_URL}/api/config/role-models",
                timeout=30
            )
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text[:1000]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n解析后的数据:")
                    print(f"  success: {data.get('success')}")
                    print(f"  message: {data.get('message')}")
                    if data.get('success') and data.get('data'):
                        role_data = data['data']
                        print(f"  data:")
                        print(f"    - 分析师: {len(role_data.get('analysts', []))}")
                        print(f"    - 辩论者: {len(role_data.get('debaters', []))}")
                        print(f"    - 决策者: {len(role_data.get('decision_makers', []))}")
                        return True
                    else:
                        print(f"  ❌ 失败: {data.get('message')}")
                        return False
                except Exception as e:
                    print(f"  ❌ JSON 解析失败: {e}")
                    return False
            else:
                print(f"  ❌ 状态码错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ 请求异常: {e}")
            traceback.print_exc()
            return False

async def test_get_presets():
    """测试获取预设列表 - 详细版"""
    print("\n=== 测试获取预设列表 ===")
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"发送请求: GET {BASE_URL}/api/config/model-presets")
            response = await client.get(
                f"{BASE_URL}/api/config/model-presets",
                timeout=30
            )
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:1000]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n解析后的数据:")
                    print(f"  success: {data.get('success')}")
                    if data.get('success'):
                        presets = data.get('data', [])
                        print(f"  预设数量: {len(presets)}")
                        return True
                    else:
                        print(f"  失败: {data.get('message')}")
                        return False
                except Exception as e:
                    print(f"  JSON 解析失败: {e}")
                    return False
            else:
                print(f"  状态码错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  请求异常: {e}")
            traceback.print_exc()
            return False

async def main():
    print("=" * 60)
    print("详细 API 测试")
    print("=" * 60)
    
    results = []
    results.append(("获取角色配置", await test_get_role_configs()))
    results.append(("获取预设列表", await test_get_presets()))
    
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
