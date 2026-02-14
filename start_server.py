"""
启动服务器脚本
"""
import sys
import os

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目路径
sys.path.insert(0, r'd:\trade\TradingAgents-CN')

# 导入并启动
from app.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 启动服务器...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
