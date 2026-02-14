#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
端到端测试：调用后端API验证prompt保存功能
用法: python test_api_e2e.py
"""

import sys
import time
import json
import requests
from datetime import datetime

# 配置 - 请根据实际情况修改
BASE_URL = "http://localhost:8000"  # 后端服务地址
STOCK_CODE = "000001"  # 股票代码
ANALYSIS_DATE = datetime.now().strftime("%Y-%m-%d")  # 分析日期

# 测试用户配置 - 请修改为实际的用户名和密码
TEST_USERNAME = "admin"  # 修改为实际用户名
TEST_PASSWORD = "admin123"  # 修改为实际密码

# API端点 (根据 app/main.py 中的路由注册)
LOGIN_ENDPOINT = f"{BASE_URL}/api/auth/login"
ANALYZE_ENDPOINT = f"{BASE_URL}/api/analysis/single"
STATUS_ENDPOINT = f"{BASE_URL}/api/analysis/tasks/{{task_id}}/status"
REPORT_ENDPOINT = f"{BASE_URL}/api/reports/{{task_id}}"


def login():
    """用户登录获取token"""
    print("\n[Step 0] 用户登录")
    print(f"  用户名: {TEST_USERNAME}")
    print(f"  API: {LOGIN_ENDPOINT}")
    
    payload = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_ENDPOINT, json=payload, timeout=10)
        print(f"  响应状态: {response.status_code}")
        print(f"  响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  响应JSON: {data}")
            token = data.get("access_token") or data.get("data", {}).get("access_token")
            if token:
                print(f"  [OK] 登录成功，获取到token")
                return token
            else:
                print(f"  [FAIL] 响应中未找到access_token")
                return None
        else:
            print(f"  [FAIL] 登录失败: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] 无法连接到后端服务: {BASE_URL}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def start_analysis(token):
    """启动分析任务"""
    print("\n[Step 1] 启动分析任务")
    print(f"  股票代码: {STOCK_CODE}")
    print(f"  分析日期: {ANALYSIS_DATE}")
    print(f"  API: {ANALYZE_ENDPOINT}")
    
    payload = {
        "stock_code": STOCK_CODE,
        "analysis_date": ANALYSIS_DATE,
        "parameters": {
            "selected_analysts": ["market", "fundamentals", "sentiment", "news", "bull_researcher", "bear_researcher", "risky_analyst", "safe_analyst", "neutral_analyst"],
            "research_depth": "深度",
            "quick_model": "deepseek-v3.2-exp-thinking",
            "deep_model": "deepseek-v3.2-exp-thinking"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(ANALYZE_ENDPOINT, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("data", {}).get("task_id")
            print(f"  [OK] 任务启动成功: {task_id}")
            return task_id
        else:
            print(f"  [FAIL] 任务启动失败: {response.status_code}")
            print(f"    响应: {response.text[:500]}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] 无法连接到后端服务: {BASE_URL}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def wait_for_completion(task_id, token, max_wait=300, poll_interval=10):
    """等待任务完成"""
    print(f"\n[Step 2] 等待任务完成: {task_id}")
    
    start_time = time.time()
    last_status = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    while time.time() - start_time < max_wait:
        try:
            url = STATUS_ENDPOINT.format(task_id=task_id)
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("data", {}).get("status", "unknown")
                progress = data.get("data", {}).get("progress", 0)
                
                if status != last_status:
                    print(f"  状态: {status} ({progress}%)")
                    last_status = status
                
                if status in ["completed", "success"]:
                    print(f"  [OK] 任务完成!")
                    return True
                elif status in ["failed", "error"]:
                    error_msg = data.get("data", {}).get("error", data.get("data", {}).get("message", "Unknown error"))
                    full_response = json.dumps(data, ensure_ascii=False, indent=2)
                    print(f"  [FAIL] 任务失败: {error_msg}")
                    print(f"  完整响应: {full_response}")
                    return False
                
            time.sleep(poll_interval)
        except Exception as e:
            print(f"  轮询错误: {e}")
            time.sleep(poll_interval)
    
    print(f"  [FAIL] 等待超时")
    return False


def check_prompts(task_id, token):
    """查询并验证prompts"""
    print(f"\n[Step 3] 查询任务结果: {task_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        url = REPORT_ENDPOINT.format(task_id=task_id)
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 获取成功")
            
            if isinstance(data, dict):
                report_data = data.get("data", data)
                prompts = report_data.get("prompts", {})
                print(f"  prompts类型: {type(prompts)}")
                
                if isinstance(prompts, dict):
                    analyst_prompts = [
                        'bull_researcher', 'bear_researcher',
                        'risky_analyst', 'safe_analyst', 'neutral_analyst'
                    ]
                    
                    all_found = True
                    for analyst in analyst_prompts:
                        if analyst in prompts:
                            content = prompts[analyst]
                            if content and len(str(content)) > 0:
                                print(f"    [OK] {analyst}: {len(str(content))} chars")
                            else:
                                print(f"    [FAIL] {analyst}: 空内容")
                                all_found = False
                        else:
                            print(f"    [FAIL] {analyst}: 不存在")
                            all_found = False
                    
                    return all_found
                else:
                    print(f"  [FAIL] prompts不是字典类型")
                    return False
            else:
                print(f"  [FAIL] 响应不是字典类型")
                return False
        else:
            print(f"  [FAIL] 查询失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def main():
    """主测试流程"""
    print("=" * 60)
    print("端到端测试: Prompt保存功能验证")
    print("=" * 60)
    
    # Step 0: 登录
    token = login()
    if not token:
        print("\n请检查用户名和密码是否正确")
        return 1
    
    # Step 1: 启动分析任务
    task_id = start_analysis(token)
    if not task_id:
        return 1
    
    # Step 2: 等待任务完成
    if not wait_for_completion(task_id, token):
        return 1
    
    # Step 3: 查询并验证prompts
    success = check_prompts(task_id, token)
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Prompt保存功能正常工作!")
    else:
        print("FAILED: Prompt保存功能可能存在问题")
    print("=" * 60)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
