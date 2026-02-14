"""
验证Prompt保存逻辑是否正确实现
"""
import ast
import sys

def check_file(filepath, expected_patterns):
    """检查文件是否包含预期的代码模式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = []
    for pattern_name, pattern in expected_patterns.items():
        found = pattern in content
        results.append((pattern_name, found))
        print(f"  {'✅' if found else '❌'} {pattern_name}")
    
    return all(r[1] for r in results)

def main():
    print("=" * 60)
    print("验证分析师Prompt保存逻辑")
    print("=" * 60)
    
    files_to_check = {
        "news_analyst.py": {
            "构建full_request_prompt": "full_request_prompt = \"\"",
            "保存news_request_prompt": '"news_request_prompt": full_request_prompt',
            "format_messages调用": "prompt.format_messages",
        },
        "social_media_analyst.py": {
            "构建full_request_prompt": "full_request_prompt = \"\"",
            "保存sentiment_request_prompt": '"sentiment_request_prompt": full_request_prompt',
            "format_messages调用": "prompt.format_messages",
        },
        "capital_flow_analyst.py": {
            "构建full_request_prompt": "full_request_prompt = \"\"",
            "保存capital_flow_request_prompt": '"capital_flow_request_prompt": full_request_prompt',
            "format_messages调用": "prompt.format_messages",
        },
        "fundamentals_analyst.py": {
            "构建full_request_prompt": "full_request_prompt = \"\"",
            "保存fundamentals_prompt": '"fundamentals_prompt": full_request_prompt',
            "format_messages调用": "prompt.format_messages",
        },
        "market_analyst.py": {
            "构建full_request_prompt": "full_request_prompt = \"\"",
            "保存market_request_prompt": '"market_request_prompt": full_request_prompt',
            "format_messages调用": "prompt.format_messages",
        },
    }
    
    base_path = "tradingagents/agents/analysts"
    all_passed = True
    
    for filename, patterns in files_to_check.items():
        print(f"\n📁 检查 {filename}:")
        filepath = f"{base_path}/{filename}"
        try:
            passed = check_file(filepath, patterns)
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"  ❌ 检查失败: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有文件检查通过! Prompt保存逻辑已正确实现")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分文件检查未通过，需要修复")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
