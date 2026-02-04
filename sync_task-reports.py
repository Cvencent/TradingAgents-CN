#!/usr/bin/env python3
"""
同步任务结果到MongoDB的脚本
将Redis中完整的result.reports同步到MongoDB的analysis_reports集合
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.memory_state_manager import MemoryStateManager
from app.core.database import get_mongo_db_sync
from datetime import datetime

async def sync_task_reports(task_id: str, dry_run: bool = True):
    """同步单个任务的reports到MongoDB"""
    try:
        # 1. 从Redis获取完整的result
        memory_manager = MemoryStateManager()
        result = await memory_manager.get_result_data(task_id)

        if not result:
            print(f"❌ 未找到任务 {task_id} 的结果数据")
            return False

        print(f"✅ 找到任务 {task_id} 的结果数据")
        print(f"   result中的reports键: {list(result.keys())}")

        # 2. 获取完整的reports
        reports = result.get('reports', {})
        if not reports:
            print(f"   ⚠️ result中没有reports字段或reports为空")
            return False

        print(f"   📊 reports包含 {len(reports)} 个报告: {list(reports.keys())}")

        # 3. 更新MongoDB
        db = get_mongo_db_sync()

        # 更新 analysis_reports
        update_result = db.analysis_reports.update_one(
            {'task_id': task_id},
            {'$set': {'reports': reports}}
        )

        print(f"   📄 analysis_reports 更新结果: matched={update_result.matched}, modified={update_result.modified}")

        # 更新 analysis_tasks
        tasks_update = db.analysis_tasks.update_one(
            {'task_id': task_id},
            {'$set': {'result.reports': reports}}
        )

        print(f"   📋 analysis_tasks 更新结果: matched={tasks_update.matched}, modified={tasks_update.modified}")

        return True

    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def sync_all_completed_tasks():
    """同步所有已完成任务的reports到MongoDB"""
    try:
        db = get_mongo_db_sync()
        memory_manager = MemoryStateManager()

        # 1. 获取所有已完成的任务
        completed_tasks = list(db.analysis_tasks.find(
            {'status': 'completed'},
            {'task_id': 1, 'created_at': 1}
        ))

        print(f"📊 找到 {len(completed_tasks)} 个已完成任务")

        synced_count = 0
        failed_count = 0
        skipped_count = 0

        for task in completed_tasks:
            task_id = task['task_id']
            print(f"\n🔄 处理任务: {task_id}")

            # 2. 检查MongoDB中的reports
            mongo_task = db.analysis_tasks.find_one(
                {'task_id': task_id},
                {'result.reports': 1}
            )
            mongo_reports = mongo_task.get('result', {}).get('reports', {}) if mongo_task else {}

            # 3. 从Redis获取完整result
            redis_result = await memory_manager.get_result_data(task_id)
            redis_reports = redis_result.get('reports', {}) if redis_result else {}

            # 4. 比较
            mongo_keys = set(mongo_reports.keys()) if mongo_reports else set()
            redis_keys = set(redis_reports.keys()) if redis_reports else set()

            missing_in_mongo = redis_keys - mongo_keys
            extra_in_mongo = mongo_keys - redis_keys

            if not missing_in_mongo and not extra_in_mongo:
                print(f"   ✅ 数据一致，跳过")
                skipped_count += 1
                continue

            if missing_in_mongo:
                print(f"   ⚠️ MongoDB缺失: {missing_in_mongo}")

            # 5. 同步
            if redis_reports:
                success = await sync_task_reports(task_id, dry_run=False)
                if success:
                    synced_count += 1
                    print(f"   ✅ 同步完成")
                else:
                    failed_count += 1
            else:
                print(f"   ❌ Redis中没有reports数据")
                failed_count += 1

        print(f"\n📊 同步完成:")
        print(f"   - 同步成功: {synced_count}")
        print(f"   - 同步失败: {failed_count}")
        print(f"   - 跳过: {skipped_count}")

    except Exception as e:
        print(f"❌ 批量同步失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='同步任务reports到MongoDB')
    parser.add_argument('--task-id', type=str, help='指定单个任务ID同步')
    parser.add_argument('--all', action='store_true', help='同步所有已完成任务')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际写入')

    args = parser.parse_args()

    if args.task_id:
        asyncio.run(sync_task_reports(args.task_id, dry_run=args.dry_run))
    elif args.all:
        asyncio.run(sync_all_completed_tasks())
    else:
        print("请指定 --task-id <任务ID> 或 --all")
        print("示例:")
        print("  python sync_task-reports.py --task-id 57113969-30b5-47a5-b82d-a0b41a6ee146")
        print("  python sync_task-reports.py --all --dry-run")
