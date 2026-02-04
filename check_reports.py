#!/usr/bin/env python3
"""检查报告数据保存情况的诊断脚本"""

from pymongo import MongoClient

def check_reports():
    client = MongoClient('localhost', 27017)
    db = client['tradingagents']

    task_id = "57113969-30b5-47a5-b82d-a0b41a6ee146"

    print("=" * 80)
    print(f"🔍 检查任务: {task_id}")
    print("=" * 80)

    # 1. 检查 analysis_reports
    print("\n📄 analysis_reports 集合:")
    doc = db.analysis_reports.find_one({'task_id': task_id})
    if doc:
        print(f"  ✅ 找到报告文档")
        print(f"     _id: {doc.get('_id')}")
        print(f"     analysis_id: {doc.get('analysis_id')}")
        print(f"     stock_symbol: {doc.get('stock_symbol')}")
        print(f"     task_id: {doc.get('task_id')}")

        reports = doc.get('reports', {})
        print(f"     reports字段: {type(reports)}")
        print(f"     reports中的键: {list(reports.keys()) if isinstance(reports, dict) else 'NOT_DICT'}")

        if isinstance(reports, dict):
            for key, value in reports.items():
                content_len = len(str(value)) if value else 0
                preview = str(value)[:100] if value else "EMPTY"
                print(f"       - {key}: {content_len} chars, preview: {preview}...")
    else:
        print(f"  ❌ 在analysis_reports中未找到")

    # 2. 检查 analysis_tasks
    print("\n📋 analysis_tasks 集合:")
    task = db.analysis_tasks.find_one({'task_id': task_id})
    if task:
        result = task.get('result', {})
        print(f"  ✅ 找到任务文档")
        print(f"     status: {task.get('status')}")

        result_reports = result.get('reports', {})
        print(f"     result.reports字段: {type(result_reports)}")
        print(f"     result.reports中的键: {list(result_reports.keys()) if isinstance(result_reports, dict) else 'NOT_DICT'}")

        if isinstance(result_reports, dict):
            for key, value in result_reports.items():
                content_len = len(str(value)) if value else 0
                preview = str(value)[:100] if value else "EMPTY"
                print(f"       - {key}: {content_len} chars, preview: {preview}...")
    else:
        print(f"  ❌ 在analysis_tasks中未找到")

    # 3. 对比
    print("\n🔍 数据对比:")
    if doc and task:
        reports_in_doc = doc.get('reports', {})
        reports_in_result = result.get('reports', {})

        keys_in_doc = set(reports_in_doc.keys()) if isinstance(reports_in_doc, dict) else set()
        keys_in_result = set(reports_in_result.keys()) if isinstance(reports_in_result, dict) else set()

        missing_in_doc = keys_in_result - keys_in_doc
        missing_in_result = keys_in_doc - keys_in_result

        if missing_in_doc:
            print(f"  ⚠️ 在analysis_reports中缺失: {missing_in_doc}")
        else:
            print(f"  ✅ analysis_reports包含所有reports")
    else:
        print(f"  ❌ 无法对比，缺少部分数据")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_reports()
