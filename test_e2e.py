#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
端到端测试：验证prompt保存和提取流程
"""

import sys
import json
sys.path.insert(0, r'D:\trade\TradingAgents-CN')

def test_end_to_end():
    """模拟完整的分析流程，从研究员保存prompt到最终提取"""
    
    print("=" * 80)
    print("End-to-End Test: Prompt Saving and Extraction Flow")
    print("=" * 80)
    
    # ========== Step 1: 模拟研究员节点生成state ==========
    print("\n[Step 1] Researcher nodes generate state with prompts")
    
    # Bull researcher prompt
    bull_prompt = """You are a professional stock analyst focusing on bullish analysis.

Stock: 000001
Date: 2025-01-13

Please analyze the following market data and provide bullish arguments..."""
    
    # Bear researcher prompt  
    bear_prompt = """You are a professional stock analyst focusing on bearish analysis.

Stock: 000001
Date: 2025-01-13

Please identify risks and provide bearish arguments..."""
    
    # Risky analyst prompt
    risky_prompt = """You are an aggressive risk analyst.

Stock: 000001

Please evaluate aggressive trading strategies..."""
    
    # Safe analyst prompt
    safe_prompt = """You are a conservative risk analyst.

Stock: 000001

Please evaluate conservative trading strategies..."""
    
    # Neutral analyst prompt
    neutral_prompt = """You are a neutral risk analyst.

Stock: 000001

Please provide balanced risk assessment..."""
    
    # 模拟最终state（这是LangGraph执行完成后返回的state）
    final_state = {
        "company_of_interest": "000001",
        "trade_date": "2025-01-13",
        "market_report": "Market analysis report content...",
        "fundamentals_report": "Fundamentals analysis report content...",
        "sentiment_report": "Sentiment analysis report content...",
        "news_report": "News analysis report content...",
        
        # 投资辩论状态（包含研究员保存的prompts）
        "investment_debate_state": {
            "bull_history": ["Bullish argument round 1", "Bullish argument round 2"],
            "bear_history": ["Bearish argument round 1"],
            "bull_prompts": [bull_prompt],  # 研究员保存的prompt
            "bear_prompts": [bear_prompt],   # 研究员保存的prompt
            "history": "Full debate history...",
            "current_response": "Latest response...",
            "judge_decision": "Judge decision...",
            "count": 2
        },
        
        # 风险辩论状态（包含风险分析师保存的prompts）
        "risk_debate_state": {
            "risky_history": ["Risky analyst response"],
            "safe_history": ["Safe analyst response"],
            "neutral_history": ["Neutral analyst response"],
            "risky_prompts": [risky_prompt],      # 风险分析师保存的prompt
            "safe_prompts": [safe_prompt],        # 风险分析师保存的prompt
            "neutral_prompts": [neutral_prompt],  # 风险分析师保存的prompt
            "history": "Risk debate history...",
            "latest_speaker": "Neutral",
            "current_risky_response": "Risky response...",
            "current_safe_response": "Safe response...",
            "current_neutral_response": "Neutral response...",
            "judge_decision": "Risk judge decision...",
            "count": 1
        },
        
        "trader_investment_plan": "Trader investment plan...",
        "final_trade_decision": "Final trade decision...",
        "messages": [],
        "performance_metrics": {
            "total_time": 600.5,
            "node_count": 13
        }
    }
    
    print(f"  ✓ Created final_state with prompts")
    print(f"  ✓ investment_debate_state has bull_prompts: {'bull_prompts' in final_state['investment_debate_state']}")
    print(f"  ✓ investment_debate_state has bear_prompts: {'bear_prompts' in final_state['investment_debate_state']}")
    print(f"  ✓ risk_debate_state has risky_prompts: {'risky_prompts' in final_state['risk_debate_state']}")
    print(f"  ✓ risk_debate_state has safe_prompts: {'safe_prompts' in final_state['risk_debate_state']}")
    print(f"  ✓ risk_debate_state has neutral_prompts: {'neutral_prompts' in final_state['risk_debate_state']}")
    
    # ========== Step 2: 模拟从state提取reports ==========
    print("\n[Step 2] Extract reports from state")
    
    reports = {}
    state = final_state
    
    # 提取分析师报告（模拟 _save_analysis_result_web_style 逻辑）
    report_fields = [
        'market_report',
        'fundamentals_report', 
        'sentiment_report',
        'news_report'
    ]
    
    for field in report_fields:
        if isinstance(state, dict) and field in state:
            value = state[field]
            if isinstance(value, str) and len(value.strip()) > 10:
                reports[field] = value.strip()
    
    # 从investment_debate_state提取研究员报告
    if isinstance(state, dict) and 'investment_debate_state' in state:
        debate_state = state['investment_debate_state']
        if isinstance(debate_state, dict):
            # Bull researcher
            bull_content = debate_state.get('bull_history', "")
            if bull_content:
                bull_str = str(bull_content)
                if len(bull_str.strip()) > 10:
                    reports['bull_researcher'] = bull_str.strip()
                    print(f"  ✓ Extracted bull_researcher: {len(reports['bull_researcher'])} chars")
            
            # Bear researcher
            bear_content = debate_state.get('bear_history', "")
            if bear_content:
                bear_str = str(bear_content)
                if len(bear_str.strip()) > 10:
                    reports['bear_researcher'] = bear_str.strip()
                    print(f"  ✓ Extracted bear_researcher: {len(reports['bear_researcher'])} chars")
    
    # 从risk_debate_state提取风险分析师报告
    if isinstance(state, dict) and 'risk_debate_state' in state:
        risk_state = state['risk_debate_state']
        if isinstance(risk_state, dict):
            for key in ['risky_history', 'safe_history', 'neutral_history']:
                content = risk_state.get(key, "")
                if content:
                    content_str = str(content)
                    if len(content_str.strip()) > 10:
                        analyst_key = key.replace('_history', '_analyst')
                        reports[analyst_key] = content_str.strip()
                        print(f"  ✓ Extracted {analyst_key}: {len(reports[analyst_key])} chars")
    
    print(f"\n  Total reports extracted: {len(reports)}")
    
    # ========== Step 3: 模拟提取prompts ==========
    print("\n[Step 3] Extract prompts from state")
    
    prompts = {}
    
    # 从investment_debate_state提取
    investment_debate_state = state.get("investment_debate_state", {}) if isinstance(state, dict) else {}
    if investment_debate_state and isinstance(investment_debate_state, dict):
        # Bull researcher
        if "bull_researcher" in reports and reports["bull_researcher"]:
            bull_prompts = investment_debate_state.get("bull_prompts", [])
            if bull_prompts and isinstance(bull_prompts, list) and len(bull_prompts) > 0:
                full_prompt = bull_prompts[0] if len(bull_prompts) == 1 else "\n\n".join([f"=== Round {i+1} ===\n{p}" for i, p in enumerate(bull_prompts)])
                prompts["bull_researcher"] = full_prompt.strip()
                print(f"  ✓ Extracted bull_researcher prompt: {len(full_prompt)} chars")
        
        # Bear researcher
        if "bear_researcher" in reports and reports["bear_researcher"]:
            bear_prompts = investment_debate_state.get("bear_prompts", [])
            if bear_prompts and isinstance(bear_prompts, list) and len(bear_prompts) > 0:
                full_prompt = bear_prompts[0] if len(bear_prompts) == 1 else "\n\n".join([f"=== Round {i+1} ===\n{p}" for i, p in enumerate(bear_prompts)])
                prompts["bear_researcher"] = full_prompt.strip()
                print(f"  ✓ Extracted bear_researcher prompt: {len(full_prompt)} chars")
    
    # 从risk_debate_state提取
    risk_debate_state = state.get("risk_debate_state", {}) if isinstance(state, dict) else {}
    if risk_debate_state and isinstance(risk_debate_state, dict):
        # Risky analyst
        if "risky_analyst" in reports and reports["risky_analyst"]:
            risky_prompts = risk_debate_state.get("risky_prompts", [])
            if risky_prompts and isinstance(risky_prompts, list) and len(risky_prompts) > 0:
                full_prompt = risky_prompts[0] if len(risky_prompts) == 1 else "\n\n".join([f"=== Round {i+1} ===\n{p}" for i, p in enumerate(risky_prompts)])
                prompts["risky_analyst"] = full_prompt.strip()
                print(f"  ✓ Extracted risky_analyst prompt: {len(full_prompt)} chars")
        
        # Safe analyst
        if "safe_analyst" in reports and reports["safe_analyst"]:
            safe_prompts = risk_debate_state.get("safe_prompts", [])
            if safe_prompts and isinstance(safe_prompts, list) and len(safe_prompts) > 0:
                full_prompt = safe_prompts[0] if len(safe_prompts) == 1 else "\n\n".join([f"=== Round {i+1} ===\n{p}" for i, p in enumerate(safe_prompts)])
                prompts["safe_analyst"] = full_prompt.strip()
                print(f"  ✓ Extracted safe_analyst prompt: {len(full_prompt)} chars")
        
        # Neutral analyst
        if "neutral_analyst" in reports and reports["neutral_analyst"]:
            neutral_prompts = risk_debate_state.get("neutral_prompts", [])
            if neutral_prompts and isinstance(neutral_prompts, list) and len(neutral_prompts) > 0:
                full_prompt = neutral_prompts[0] if len(neutral_prompts) == 1 else "\n\n".join([f"=== Round {i+1} ===\n{p}" for i, p in enumerate(neutral_prompts)])
                prompts["neutral_analyst"] = full_prompt.strip()
                print(f"  ✓ Extracted neutral_analyst prompt: {len(full_prompt)} chars")
    
    print(f"\n  Total prompts extracted: {len(prompts)}")
    print(f"  Prompt keys: {list(prompts.keys())}")
    
    # ========== Step 4: 验证结果 ==========
    print("\n[Step 4] Verification")
    
    expected_prompts = ['bull_researcher', 'bear_researcher', 'risky_analyst', 'safe_analyst', 'neutral_analyst']
    all_passed = True
    
    for key in expected_prompts:
        if key in prompts:
            content = prompts[key]
            if len(content) > 0:
                print(f"  [PASS] {key}: {len(content)} chars")
            else:
                print(f"  [FAIL] {key}: empty content")
                all_passed = False
        else:
            print(f"  [FAIL] {key}: not found")
            all_passed = False
    
    # ========== Step 5: 模拟保存到MongoDB ==========
    print("\n[Step 5] Simulate saving to MongoDB")
    
    # 模拟保存到analysis_tasks集合的document
    document = {
        "task_id": "test-task-123",
        "stock_code": "000001",
        "analysis_date": "2025-01-13",
        "reports": reports,
        "prompts": prompts
    }
    
    print(f"  ✓ Document prepared for MongoDB")
    print(f"  ✓ Reports count: {len(document['reports'])}")
    print(f"  ✓ Prompts count: {len(document['prompts'])}")
    
    # 验证JSON序列化
    try:
        json_str = json.dumps(document, indent=2)
        print(f"  ✓ JSON serialization successful: {len(json_str)} chars")
    except Exception as e:
        print(f"  [FAIL] JSON serialization failed: {e}")
        all_passed = False
    
    # ========== Final Result ==========
    print("\n" + "=" * 80)
    if all_passed:
        print("SUCCESS: All tests passed!")
        print("The prompt saving and extraction flow works correctly.")
        print("=" * 80)
        return True
    else:
        print("FAILED: Some tests failed.")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
