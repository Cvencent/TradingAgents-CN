#!/usr/bin/env python3
"""测试后端API是否能从MongoDB获取报告数据"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_mongo_db
from app.core.config import settings

async def test_api_mongodb():
    print("[TEST] 初始化数据库连接...")
    try:
        await init_db()
        print("[OK] 数据库初始化成功")

        db = get_mongo_db()
        print(f"[INFO] 数据库名称: {db.name}")

        task_id = "50f8e5b4-6e62-4fee-a580-735b29bf4f35"
        print(f"\n[TEST] 查询报告详情: {task_id}")

        # 测试 reports API 的查询逻辑
        doc = await db.analysis_reports.find_one({'task_id': task_id})

        if doc:
            print(f"[OK] 找到报告文档")
            reports = doc.get('reports', {})
            print(f"[INFO] 报告数量: {len(reports)}")
            print(f"[INFO] 报告键: {list(reports.keys())}")

            bull = reports.get('bull_researcher', '')
            print(f"\n[INFO] bull_researcher 长度: {len(bull)}")
            print(f"[INFO] bull_researcher 预览: {bull[:300]}...")
        else:
            print("[FAIL] 未找到报告文档")

            # 尝试从 analysis_tasks 获取
            print("\n[TEST] 尝试从 analysis_tasks 获取...")
            task = await db.analysis_tasks.find_one({'task_id': task_id})
            if task:
                result = task.get('result', {})
                reports = result.get('reports', {})
                print(f"[OK] analysis_tasks 中有 {len(reports)} 个报告")
                print(f"[INFO] 报告键: {list(reports.keys())}")
            else:
                print("[FAIL] analysis_tasks 中也未找到")

    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"[INFO] MONGO_URI: {settings.MONGO_URI}")
    print(f"[INFO] MONGO_DB: {settings.MONGO_DB}")
    asyncio.run(test_api_mongodb())
