"""
简单测试服务是否可用
"""
import requests
import sys

BASE_URL = "http://localhost:8001"

def test_health():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"   状态码: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ 服务正常运行!")
            return True
        else:
            print(f"❌ 服务返回错误: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_login():
    """测试登录接口"""
    print("\n🔐 测试登录接口...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )
        print(f"   状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("data", {}).get("access_token")
            print(f"✅ 登录成功! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("测试服务可用性")
    print("=" * 60)

    if not test_health():
        print("\n❌ 服务不可用，退出测试")
        sys.exit(1)

    token = test_login()
    if not token:
        print("\n❌ 登录失败，退出测试")
        sys.exit(1)

    print("\n✅ 所有测试通过!")
