"""
端到端测试：验证Prompt保存和提取功能
使用admin用户token
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

# 使用admin用户的JWT token (有效期1小时)
HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MDg4NjA2Mn0.cdT7gcYZ2-Vi-GEa3D8JCHXMWx9yDmMbfWKHwp6RrRk",
    "Content-Type": "application/json"
}

def wait_for_service(max_wait=120):
    """等待服务就绪"""
    print("⏳ 等待后端服务就绪...")
    for i in range(max_wait):
        try:
            resp = requests.get(f"{BASE_URL}/api/health", headers=HEADERS, timeout=2)
            if resp.status_code == 200:
                print(f"✅ 服务已就绪! (等待了 {i} 秒)")
                return True
        except:
            pass
        if i % 10 == 0:
            print(f"  还在等待... ({i}秒)")
        time.sleep(1)
    print("❌ 等待超时")
    return False

def run_test():
    """运行完整测试"""
    print("\n" + "="*60)
    print("🧪 开始测试股票 300033 的Prompt提取功能")
    print("="*60)

    # 测试参数 - 只使用market和fundamentals
    test_params = {
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

    # 1. 创建分析任务
    print("\n[1/4] 创建分析任务...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/analysis/single",
            json=test_params,
            headers=HEADERS,
            timeout=30
        )
        print(f"  状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ 错误: {resp.text[:500]}")
            return False
        result = resp.json()
        task_id = result.get("task_id")
        print(f"  ✅ 任务创建成功: {task_id}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        return False

    # 2. 等待分析完成
    print("\n[2/4] 等待分析完成...")
    for i in range(120):  # 最多等待120次，每次5秒 = 600秒
        try:
            resp = requests.get(
                f"{BASE_URL}/api/analysis/status/{task_id}",
                headers=HEADERS,
                timeout=10
            )
            if resp.status_code == 200:
                status = resp.json().get("status")
                if i % 6 == 0:  # 每30秒打印一次
                    print(f"  状态: {status} (已等待 {i*5}秒)")
                if status == "completed":
                    print("  ✅ 分析完成!")
                    break
                elif status == "failed":
                    print("  ❌ 分析失败!")
                    return False
            time.sleep(5)
        except Exception as e:
            print(f"  检查异常: {e}")
            time.sleep(5)
    else:
        print("  ⏱️ 等待超时!")
        return False

    # 3. 获取报告ID
    print("\n[3/4] 获取报告ID...")
    try:
        resp = requests.get(
            f"{BASE_URL}/api/analysis/tasks/{task_id}",
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code == 200:
            task_data = resp.json()
            report_id = task_data.get("result", {}).get("analysis_id") or task_id
            print(f"  ✅ 报告ID: {report_id}")
        else:
            report_id = task_id
            print(f"  ⚠️ 使用task_id: {report_id}")
    except Exception as e:
        report_id = task_id
        print(f"  ⚠️ 使用task_id: {report_id}")

    # 4. 查看Prompts
    print("\n[4/4] 查看Prompts...")
    time.sleep(2)
    try:
        resp = requests.get(
            f"{BASE_URL}/api/reports/{report_id}/prompts",
            headers=HEADERS,
            timeout=10
        )
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            prompts = data.get("prompts", [])
            warning = data.get("warning", "")

            print(f"\n{'='*60}")
            print(f"📊 结果汇总:")
            print(f"  - Prompts数量: {len(prompts)}")
            print(f"  - 警告: {warning or '无'}")
            print(f"{'='*60}")

            if prompts:
                print("\n📋 Prompts详情:")
                all_original = True
                for i, p in enumerate(prompts):
                    content = p.get('content', '')
                    analyst = p.get('analyst', 'unknown')
                    # 判断是否为原始prompt
                    is_extracted = content.startswith('[从messages提取]') or content.startswith('[从report提取]')
                    is_original = not is_extracted
                    if not is_original:
                        all_original = False
                    status = "✅ 原始" if is_original else "⚠️ 提取"
                    print(f"\n  {i+1}. {analyst}: {len(content)} 字符 [{status}]")
                    # 显示前300字符
                    preview = content[:300].replace('\n', ' ')
                    print(f"     预览: {preview}...")
                
                print(f"\n{'='*60}")
                if all_original:
                    print("🎉 测试通过! 所有Prompt都是原始保存的!")
                else:
                    print("⚠️ 部分Prompt是从messages提取的，需要检查")
                print(f"{'='*60}")
                return all_original
            else:
                print("\n  ❌ 没有提取到任何Prompts!")
                return False
        else:
            print(f"  ❌ 获取失败: {resp.text[:500]}")
            return False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if wait_for_service():
        success = run_test()
        sys.exit(0 if success else 1)
    else:
        sys.exit(1)
