
"""测试配置读取"""
from app.core.config import settings

print(f"PORT: {settings.PORT}")
print(f"HOST: {settings.HOST}")
print(f"DEBUG: {settings.DEBUG}")
