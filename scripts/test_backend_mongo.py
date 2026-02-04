#!/usr/bin/env python3
"""测试后端是否能正确从远程MongoDB获取数据"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongo_db

async def test_mongodb():
    print("[TEST] 测试后端 MongoDB 连接...")
    try:
        db = get_mongo_db()
        print(f"[OK] MongoDB 连接成功")
        print(f"[INFO] 数据库名称: {db.name}")

        task_id = "50f8e5b4-6e62-4fee-a580-735b29bf4f35"
        print(f"\n[TEST] 查询任务: {task_id}")

        task = await db.analysis_tasks.find_one({'task_id': task_id})
        if task:
            print(f"[OK] analysis_tasks 找到任务")
            result = task.get('result', {})
            reports = result.get('reports', {})
            print(f"   报告数量: {len(reports)}")
            print(f"   报告键: {list(reports.keys())}")
        else:
            print("[FAIL] analysis_tasks 未找到任务")

        report = await db.analysis_reports.find_one({'task_id': task_id})
        if report:
            print(f"\n[OK] analysis_reports 找到报告")
            reports = report.get('reports', {})
            print(f"   报告数量: {len(reports)}")
            print(f"   报告键: {list(reports.keys())}")

            bull = reports.get('bull_researcher', '')
            print(f"\n   bull_researcher 长度: {len(bull)}")
            print(f"   bull_researcher 预览: {bull[:200]}...")
        else:
            print("\n[FAIL] analysis_reports 未找到报告")

    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mongodb())
