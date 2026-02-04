#!/usr/bin/env python3
"""
诊断分析报告数据一致性问题的脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from datetime import datetime, timedelta

async def diagnose_report_issues():
    """诊断报告数据问题"""
    
    try:
        db = get_mongo_db_sync()
        
        print("=" * 80)
        print("🔍 分析报告数据一致性诊断")
        print("=" * 80)
        
        # 1. 统计两个集合的数据量
        print("\n📊 数据统计:")
        tasks_count = db.analysis_tasks.count_documents({})
        completed_tasks_count = db.analysis_tasks.count_documents({'status': 'completed'})
        reports_count = db.analysis_reports.count_documents({})
        
        print(f"  - analysis_tasks 总数: {tasks_count}")
        print(f"  - analysis_tasks 已完成: {completed_tasks_count}")
        print(f"  - analysis_reports 总数: {reports_count}")
        print(f"  - 差异数: {completed_tasks_count - reports_count}")
        
        # 2. 检查最近的已完成任务
        print("\n📋 最近5个已完成任务:")
        recent_tasks = list(db.analysis_tasks.find(
            {'status': 'completed'}
        ).sort('completed_at', -1).limit(5))
        
        for i, task in enumerate(recent_tasks, 1):
            task_id = task.get('task_id', 'N/A')
            stock_code = task.get('stock_code', 'N/A')
            completed_at = task.get('completed_at', 'N/A')
            result = task.get('result', {})
            
            # 检查result中是否有reports
            has_reports = bool(result.get('reports'))
            has_analysis_id = bool(result.get('analysis_id'))
            
            # 检查analysis_reports中是否存在
            report_exists = db.analysis_reports.find_one({'task_id': task_id}) is not None
            
            print(f"\n  {i}. 任务ID: {task_id}")
            print(f"     股票代码: {stock_code}")
            print(f"     完成时间: {completed_at}")
            print(f"     result中有reports: {'✅' if has_reports else '❌'}")
            print(f"     result中有analysis_id: {'✅' if has_analysis_id else '❌'}")
            print(f"     analysis_reports中存在: {'✅' if report_exists else '❌'}")
            
            if not report_exists:
                print(f"     ⚠️ 警告: 任务完成但报告未保存到analysis_reports!")
        
        # 3. 检查analysis_reports中最近的数据
        print("\n📄 最近5个analysis_reports:")
        recent_reports = list(db.analysis_reports.find().sort('created_at', -1).limit(5))
        
        for i, report in enumerate(recent_reports, 1):
            analysis_id = report.get('analysis_id', 'N/A')
            stock_symbol = report.get('stock_symbol', 'N/A')
            task_id = report.get('task_id', 'N/A')
            analysis_date = report.get('analysis_date', 'N/A')
            has_reports = bool(report.get('reports'))
            
            print(f"\n  {i}. 分析ID: {analysis_id}")
            print(f"     股票代码: {stock_symbol}")
            print(f"     任务ID: {task_id}")
            print(f"     分析日期: {analysis_date}")
            print(f"     有reports数据: {'✅' if has_reports else '❌'}")
        
        # 4. 查找不一致的数据
        print("\n🔧 数据一致性检查:")
        
        # 获取所有已完成任务的ID
        completed_task_ids = set()
        for task in db.analysis_tasks.find({'status': 'completed'}, {'task_id': 1}):
            if task.get('task_id'):
                completed_task_ids.add(task['task_id'])
        
        # 获取所有报告的task_id
        report_task_ids = set()
        for report in db.analysis_reports.find({}, {'task_id': 1}):
            if report.get('task_id'):
                report_task_ids.add(report['task_id'])
        
        # 找出不匹配的数据
        missing_in_reports = completed_task_ids - report_task_ids
        orphaned_reports = report_task_ids - completed_task_ids
        
        if missing_in_reports:
            print(f"\n  ❌ 在analysis_tasks中完成但在analysis_reports中缺失的任务:")
            for tid in list(missing_in_reports)[:5]:
                task = db.analysis_tasks.find_one({'task_id': tid})
                if task:
                    print(f"     - {tid} (股票: {task.get('stock_code', 'N/A')})")
            if len(missing_in_reports) > 5:
                print(f"     ... 还有 {len(missing_in_reports) - 5} 个")
        
        if orphaned_reports:
            print(f"\n  ⚠️ 在analysis_reports中存在但任务已删除的报告:")
            for tid in list(orphaned_reports)[:5]:
                print(f"     - task_id: {tid}")
        
        if not missing_in_reports and not orphaned_reports:
            print("\n  ✅ 数据一致性良好")
        
        # 5. 检查日期字段问题
        print("\n📅 日期字段检查:")
        
        # 检查analysis_tasks中result.analysis_date为None或空的情况
        tasks_with_empty_date = list(db.analysis_tasks.find({
            'status': 'completed',
            '$or': [
                {'result.analysis_date': None},
                {'result.analysis_date': ''},
                {'result': {'$exists': False}}
            ]
        }).limit(5))
        
        if tasks_with_empty_date:
            print(f"\n  ⚠️ 发现 {len(tasks_with_empty_date)} 个任务缺少analysis_date:")
            for task in tasks_with_empty_date:
                print(f"     - {task.get('task_id')}: analysis_date = {task.get('result', {}).get('analysis_date')}")
        else:
            print("\n  ✅ 所有任务都有analysis_date")
        
        # 6. 检查analysis_reports中是否有created_at字段
        reports_without_created_at = db.analysis_reports.count_documents({
            'created_at': {'$exists': False}
        })
        
        if reports_without_created_at > 0:
            print(f"\n  ❌ 发现 {reports_without_created_at} 个报告缺少created_at字段")
        else:
            print("\n  ✅ 所有报告都有created_at字段")
        
        print("\n" + "=" * 80)
        print("诊断完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 诊断过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_report_issues())
