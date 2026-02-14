"""
测试脚本：验证单股分析的prompt保存和提取功能

使用方法：
1. 确保后端服务已启动
2. 运行此脚本进行测试分析
3. 分析完成后，通过API查看prompts

分析接口：POST /api/analysis/single
查看prompt接口：GET /api/reports/{report_id}/prompts
"""

import requests
import json
import time
import sys

# API配置
BASE_URL = "http://localhost:8001"
ANALYSIS_URL = f"{BASE_URL}/api/analysis/single"

# 认证头（初始为空，登录后填充）
HEADERS = {
    "Content-Type": "application/json"
}

def login():
    """登录获取真实token"""
    print("🔐 正在登录获取token...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("data", {}).get("access_token")
            print(f"✅ 登录成功!")
            return token
        else:
            print(f"❌ 登录失败: {resp.text[:500]}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

# 测试参数
TEST_SYMBOL = "300033"
TEST_PARAMS = {
    "symbol": TEST_SYMBOL,
    "stock_code": TEST_SYMBOL,
    "parameters": {
        "market_type": "A股",
        "analysis_date": "2026-02-11",
        "research_depth": "快速",
        "selected_analysts": ["market", "fundamentals", "sentiment", "news"],
        "include_sentiment": True,
        "include_risk": True,
        "language": "zh-CN",
        "quick_analysis_model": "deepseek-v3.2-exp-thinking",
        "deep_analysis_model": "deepseek-v3.2-exp-thinking",
        "analysis_level": 1
    }
}

def test_analysis_and_prompts():
    """测试分析流程和prompt提取"""
    print("=" * 60)
    print(f"开始测试股票 {TEST_SYMBOL} 的分析流程")
    print("=" * 60)

    # 先登录获取token
    token = login()
    if not token:
        print("[X] 登录失败，无法继续测试")
        return False
    HEADERS["Authorization"] = f"Bearer {token}"

    # 步骤1：创建分析任务
    print("\n[1/4] 创建分析任务...")
    try:
        response = requests.post(
            ANALYSIS_URL,
            json=TEST_PARAMS,
            headers=HEADERS,
            timeout=10
        )
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")

        if response.status_code != 200:
            print(f"[X] 创建分析任务失败: {response.text}")
            return False

        result = response.json()
        task_id = result.get("data", {}).get("task_id")
        if not task_id:
            print(f"[X] 响应中没有task_id: {result}")
            return False

        print(f"[OK] 分析任务创建成功: {task_id}")

    except Exception as e:
        print(f"[X] 请求异常: {e}")
        return False

    # 步骤2：等待分析完成
    print("\n[2/4] 等待分析完成...")
    max_wait = 300  # 最多等待300秒
    wait_interval = 5
    waited = 0

    while waited < max_wait:
        try:
            status_url = f"{BASE_URL}/api/analysis/status/{task_id}"
            response = requests.get(status_url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                print(f"  任务状态: {status} (已等待 {waited}秒)")

                if status == "completed":
                    print(f"[OK] 分析完成!")
                    break
                elif status == "failed":
                    print(f"[X] 分析失败: {status_data.get('error', '未知错误')}")
                    return False

            time.sleep(wait_interval)
            waited += wait_interval

        except Exception as e:
            print(f"  检查状态异常: {e}")
            time.sleep(wait_interval)
            waited += wait_interval

    if waited >= max_wait:
        print(f"[X] 等待超时")
        return False

    # 步骤3：获取报告ID
    print("\n[3/4] 获取报告信息...")
    try:
        # 从任务结果中获取报告ID
        task_url = f"{BASE_URL}/api/analysis/tasks/{task_id}"
        response = requests.get(task_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            task_data = response.json()
            result = task_data.get("result", {})
            report_id = result.get("analysis_id") or task_id
            print(f"[OK] 报告ID: {report_id}")
        else:
            report_id = task_id
            print(f"[!] 无法获取任务详情，使用task_id作为report_id: {report_id}")

    except Exception as e:
        report_id = task_id
        print(f"[!] 获取任务详情异常，使用task_id: {report_id}")

    # 步骤4：查看prompts
    print("\n[4/4] 查看分析prompts...")
    time.sleep(2)  # 等待数据保存

    try:
        prompts_url = f"{BASE_URL}/api/reports/{report_id}/prompts"
        response = requests.get(prompts_url, headers=HEADERS, timeout=10)
        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            prompts_data = response.json()
            print(f"\nPrompts响应:")
            print(json.dumps(prompts_data, indent=2, ensure_ascii=False)[:2000])

            # 检查结果
            data = prompts_data.get("data", {})
            prompts = data.get("prompts", [])
            warning = data.get("warning", "")

            print(f"\n{'='*60}")
            print(f"分析结果:")
            print(f"  - Prompts数量: {len(prompts)}")
            print(f"  - 警告信息: {warning if warning else '无'}")

            if len(prompts) == 0:
                print(f"\n[X] 问题确认: 没有提取到任何prompts!")
                print(f"  可能原因:")
                print(f"  1. messages字段为空或未保存")
                print(f"  2. prompts提取逻辑有问题")
                print(f"  3. 分析过程中没有生成messages")
                return False
            else:
                print(f"\n[OK] 成功提取到 {len(prompts)} 个prompts!")
                for i, p in enumerate(prompts):
                    content = p.get('content', '')
                    is_extracted = content.startswith('[从messages提取]') or content.startswith('[从report提取]')
                    status = "⚠️ 提取的" if is_extracted else "✅ 原始的"
                    print(f"  {i+1}. {p.get('analyst', 'unknown')}: {len(content)} 字符 {status}")
                    # 显示前200字符预览
                    preview = content[:200].replace('\n', ' ')
                    print(f"     预览: {preview}...")
                return True
        else:
            print(f"[X] 获取prompts失败: {response.text}")
            return False

    except Exception as e:
        print(f"[X] 获取prompts异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_report_structure():
    """检查报告数据结构"""
    print("\n" + "=" * 60)
    print("检查报告数据结构")
    print("=" * 60)

    # 这里可以添加代码来直接查询MongoDB检查数据结构
    print("请手动检查MongoDB中的analysis_reports集合")
    print("需要检查的字段: messages, prompts, reports")

if __name__ == "__main__":
    success = test_analysis_and_prompts()

    if not success:
        print("\n" + "=" * 60)
        print("测试发现问题，需要修复!")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("测试通过!")
        print("=" * 60)
        sys.exit(0)
