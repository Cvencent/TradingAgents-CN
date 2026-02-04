#!/usr/bin/env python3
"""
数据修复脚本：将analysis_tasks中的已完成任务同步到analysis_reports集合
用于修复"任务中心有数据但报告列表没有"的问题
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync

# 设置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_missing_reports(dry_run: bool = True):
    """
    将analysis_tasks中已完成但analysis_reports中缺失的任务同步过去
    
    Args:
        dry_run: 如果为True，只显示将要执行的操作，不实际写入数据库
    """
    
    try:
        db = get_mongo_db_sync()
        
        logger.info("=" * 80)
        logger.info("🔧 开始同步缺失的报告数据")
        logger.info(f"📋 运行模式: {'预览模式(不写入)' if dry_run else '实际写入模式'}")
        logger.info("=" * 80)
        
        # 1. 获取所有已完成的任务
        logger.info("\n📊 步骤1: 获取所有已完成的任务...")
        completed_tasks = list(db.analysis_tasks.find(
            {'status': 'completed'},
            {'task_id': 1, 'stock_code': 1, 'completed_at': 1, 'result': 1, 'created_at': 1}
        ))
        logger.info(f"  ✅ 找到 {len(completed_tasks)} 个已完成任务")
        
        # 2. 获取所有已有task_id的报告
        logger.info("\n📊 步骤2: 获取analysis_reports中已有的报告...")
        existing_reports = list(db.analysis_reports.find(
            {},
            {'task_id': 1, 'analysis_id': 1}
        ))
        existing_task_ids = {r.get('task_id') for r in existing_reports if r.get('task_id')}
        logger.info(f"  ✅ 找到 {len(existing_task_ids)} 个已有报告")
        
        # 3. 找出缺失的任务
        logger.info("\n📊 步骤3: 找出缺失的报告...")
        missing_tasks = []
        for task in completed_tasks:
            task_id = task.get('task_id')
            if task_id and task_id not in existing_task_ids:
                result = task.get('result', {})
                # 只同步有实际报告数据的任务
                if result and result.get('reports'):
                    missing_tasks.append(task)
        
        logger.info(f"  ✅ 找到 {len(missing_tasks)} 个缺失的报告")
        
        if not missing_tasks:
            logger.info("\n✨ 没有缺失的报告，数据一致性良好！")
            return
        
        # 4. 显示前5个缺失的任务详情
        logger.info("\n📋 缺失报告的任务详情(前5个):")
        for i, task in enumerate(missing_tasks[:5], 1):
            result = task.get('result', {})
            logger.info(f"\n  {i}. 任务ID: {task.get('task_id')}")
            logger.info(f"     股票代码: {task.get('stock_code')}")
            logger.info(f"     完成时间: {task.get('completed_at')}")
            logger.info(f"     result中analysis_id: {result.get('analysis_id')}")
            logger.info(f"     result中reports数量: {len(result.get('reports', {}))}")
        
        if len(missing_tasks) > 5:
            logger.info(f"\n     ... 还有 {len(missing_tasks) - 5} 个")
        
        # 5. 询问用户是否继续（只在非dry_run模式下）
        if not dry_run:
            logger.info("\n⚠️  即将开始写入数据库...")
            response = input("确认执行修复操作? (输入 'yes' 继续): ")
            if response.lower() != 'yes':
                logger.info("❌ 用户取消操作")
                return
        
        # 6. 同步缺失的报告
        logger.info("\n📊 步骤4: 开始同步缺失的报告...")
        synced_count = 0
        failed_count = 0
        
        for task in missing_tasks:
            try:
                task_id = task.get('task_id')
                result = task.get('result', {})
                stock_code = task.get('stock_code', result.get('stock_symbol', result.get('stock_code', 'UNKNOWN')))
                
                # 构建document
                timestamp = task.get('completed_at') or task.get('created_at') or datetime.utcnow()
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.utcnow()
                
                analysis_id = result.get('analysis_id') or f"{stock_code}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
                
                document = {
                    "analysis_id": analysis_id,
                    "task_id": task_id,
                    "stock_symbol": stock_code,
                    "stock_name": result.get('stock_name'),
                    "market_type": result.get('market_type'),
                    "model_info": result.get('model_info', 'Unknown'),
                    "analysis_date": result.get('analysis_date') or timestamp.strftime('%Y-%m-%d'),
                    "timestamp": timestamp,
                    "status": "completed",
                    "source": "api_synced",  # 标记为同步过来的数据
                    
                    # 分析结果摘要
                    "summary": result.get('summary', ''),
                    "analysts": result.get('analysts', []),
                    "research_depth": result.get('research_depth', 1),
                    
                    # 报告内容
                    "reports": result.get('reports', {}),
                    
                    # 其他字段
                    "decision": result.get('decision', {}),
                    "recommendation": result.get('recommendation', ''),
                    "confidence_score": result.get('confidence_score', 0.0),
                    "risk_level": result.get('risk_level', '中等'),
                    "key_points": result.get('key_points', []),
                    "execution_time": result.get('execution_time', 0),
                    "tokens_used": result.get('tokens_used', 0),
                    
                    # 元数据
                    "created_at": timestamp,
                    "updated_at": datetime.utcnow(),
                    "synced_at": datetime.utcnow()  # 标记同步时间
                }
                
                if not dry_run:
                    # 实际插入数据
                    insert_result = db.analysis_reports.insert_one(document)
                    if insert_result.inserted_id:
                        synced_count += 1
                        logger.info(f"  ✅ 已同步: {task_id} -> {analysis_id}")
                    else:
                        failed_count += 1
                        logger.error(f"  ❌ 同步失败: {task_id}")
                else:
                    # 预览模式，只记录日志
                    logger.info(f"  📋 [预览] 将同步: {task_id} -> {analysis_id}")
                    synced_count += 1
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ 同步任务失败: {task.get('task_id')} - {e}")
        
        # 7. 显示结果
        logger.info("\n" + "=" * 80)
        logger.info("📊 同步结果")
        logger.info("=" * 80)
        logger.info(f"  总任务数: {len(missing_tasks)}")
        logger.info(f"  成功同步: {synced_count}")
        logger.info(f"  失败数量: {failed_count}")
        
        if dry_run:
            logger.info("\n💡 这是预览模式，没有实际写入数据")
            logger.info("💡 要实际执行修复，请运行: python scripts/sync_reports.py --execute")
        else:
            logger.info("\n✅ 数据修复完成！")
            logger.info("💡 请刷新报告列表页面查看修复后的数据")
        
    except Exception as e:
        logger.error(f"❌ 同步过程中出错: {e}")
        import traceback
        traceback.print_exc()


async def check_data_consistency():
    """检查数据一致性，显示统计信息"""
    
    try:
        db = get_mongo_db_sync()
        
        logger.info("=" * 80)
        logger.info("📊 数据一致性检查报告")
        logger.info("=" * 80)
        
        # 统计analysis_tasks
        total_tasks = db.analysis_tasks.count_documents({})
        completed_tasks = db.analysis_tasks.count_documents({'status': 'completed'})
        failed_tasks = db.analysis_tasks.count_documents({'status': 'failed'})
        running_tasks = db.analysis_tasks.count_documents({'status': 'running'})
        
        logger.info("\n📋 analysis_tasks 集合统计:")
        logger.info(f"  总任务数: {total_tasks}")
        logger.info(f"  已完成: {completed_tasks}")
        logger.info(f"  运行中: {running_tasks}")
        logger.info(f"  失败: {failed_tasks}")
        
        # 统计analysis_reports
        total_reports = db.analysis_reports.count_documents({})
        reports_with_task_id = db.analysis_reports.count_documents({'task_id': {'$exists': True}})
        
        logger.info("\n📄 analysis_reports 集合统计:")
        logger.info(f"  总报告数: {total_reports}")
        logger.info(f"  有关联task_id: {reports_with_task_id}")
        
        # 计算差异
        missing_count = completed_tasks - reports_with_task_id
        
        logger.info("\n📊 一致性分析:")
        if missing_count > 0:
            logger.info(f"  ⚠️ 发现 {missing_count} 个已完成任务缺少报告")
            logger.info(f"  💡 建议运行修复脚本: python scripts/sync_reports.py")
        else:
            logger.info(f"  ✅ 数据一致性良好")
        
        # 最近数据
        logger.info("\n📅 最近完成的5个任务:")
        recent_tasks = list(db.analysis_tasks.find(
            {'status': 'completed'}
        ).sort('completed_at', -1).limit(5))
        
        for i, task in enumerate(recent_tasks, 1):
            task_id = task.get('task_id', 'N/A')
            stock_code = task.get('stock_code', 'N/A')
            has_report = db.analysis_reports.find_one({'task_id': task_id}) is not None
            logger.info(f"  {i}. {task_id} ({stock_code}) - {'✅ 有报告' if has_report else '❌ 无报告'}")
        
        logger.info("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"❌ 检查过程中出错: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='分析报告数据修复工具')
    parser.add_argument('--check', action='store_true', help='只检查数据一致性，不执行修复')
    parser.add_argument('--execute', action='store_true', help='实际执行修复（默认是预览模式）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，显示将要执行的操作')
    
    args = parser.parse_args()
    
    if args.check:
        # 只检查
        asyncio.run(check_data_consistency())
    elif args.execute:
        # 实际执行
        asyncio.run(sync_missing_reports(dry_run=False))
    else:
        # 默认预览模式
        asyncio.run(sync_missing_reports(dry_run=True))
