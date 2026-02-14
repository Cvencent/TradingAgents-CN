"""
测试导入
"""
import sys
sys.path.insert(0, r'd:\trade\TradingAgents-CN')

print("🔍 测试导入 app.main...")
try:
    from app.main import app
    print("✅ 导入成功!")
    print(f"   App类型: {type(app)}")
    print(f"   App标题: {app.title}")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
