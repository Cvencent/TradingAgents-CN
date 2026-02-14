"""
简单测试：验证Prompt提取功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
HEADERS = {
    "Authorization": "Bearer test_token",
    "Content-Type": "application/json"
}

# 测试参数 - 只使用market和fundamentals，快速完成
TEST_PARAMS = {
    "symbol": "300033",
    "stock_code": "300033",
    "parameters": {
        "market_type": "A股",
        "analysis_date": "2026-02-11",
        "research_depth": "快速",
        "selected_analysts": ["market", "fundamentals"],
        "include_sentiment": False,
        "include_risk": False,
        "language": "zh-CN",
        "quick_analysis_model": "deepseek-v3.2-exp-thinking",
        "deep_analysis_model": "deepseek-v3.2-exp-thinking",
        "analysis_level": 1
    }
}

def test():
    print("=" * 60)
    print("测试股票 300033 的Prompt提取功能")
    print("=" * 60)

    # 1. 创建分析任务
    print("\n[1] 创建分析任务...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/analysis/single",
            json=TEST_PARAMS,
            headers=HEADERS,
            timeout=30
        )
        print(f"状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"错误: {resp.text}")
            return
        result = resp.json()
        task_id = result.get("task_id")
        print(f"任务ID: {task_id}")
    except Exception as e:
        print(f"异常: {e}")
        return

    # 2. 等待分析完成
    print("\n[2] 等待分析完成...")
    for i in range(60):  # 最多等待60次，每次5秒 = 300秒
        try:
            resp = requests.get(
                f"{BASE_URL}/api/analysis/status/{task_id}",
                headers=HEADERS,
                timeout=10
            )
            if resp.status_code == 200:
                status = resp.json().get("status")
                print(f"  状态: {status} (等待 {i*5}秒)")
                if status == "completed":
                    print("✅ 分析完成!")
                    break
                elif status == "failed":
                    print("❌ 分析失败!")
                    return
            time.sleep(5)
        except Exception as e:
            print(f"  检查异常: {e}")
            time.sleep(5)
    else:
        print("⏱️ 等待超时!")
        return

    # 3. 获取报告ID
    print("\n[3] 获取报告ID...")
    try:
        resp = requests.get(
            f"{BASE_URL}/api/analysis/tasks/{task_id}",
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code == 200:
            task_data = resp.json()
            report_id = task_data.get("result", {}).get("analysis_id") or task_id
            print(f"报告ID: {report_id}")
        else:
            report_id = task_id
            print(f"使用task_id: {report_id}")
    except Exception as e:
        report_id = task_id
        print(f"使用task_id: {report_id}")

    # 4. 查看Prompts
    print("\n[4] 查看Prompts...")
    time.sleep(2)
    try:
        resp = requests.get(
            f"{BASE_URL}/api/reports/{report_id}/prompts",
            headers=HEADERS,
            timeout=10
        )
        print(f"状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            prompts = data.get("prompts", [])
            warning = data.get("warning", "")

            print(f"\n{'='*60}")
            print(f"结果汇总:")
            print(f"  - Prompts数量: {len(prompts)}")
            print(f"  - 警告: {warning or '无'}")
            print(f"{'='*60}")

            if prompts:
                print("\n📋 Prompts详情:")
                for i, p in enumerate(prompts):
                    content = p.get('content', '')
                    analyst = p.get('analyst', 'unknown')
                    # 判断是否为原始prompt
                    is_original = not (content.startswith('[从messages提取]') or content.startswith('[从report提取]'))
                    status = "✅ 原始" if is_original else "⚠️ 提取"
                    print(f"\n  {i+1}. {analyst}: {len(content)} 字符 [{status}]")
                    # 显示前300字符
                    preview = content[:300].replace('\n', ' ')
                    print(f"     预览: {preview}...")
                print(f"\n{'='*60}")
                print("✅ 测试通过! Prompt提取功能正常")
                print(f"{'='*60}")
            else:
                print("\n❌ 没有提取到任何Prompts!")
        else:
            print(f"❌ 获取失败: {resp.text}")
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
