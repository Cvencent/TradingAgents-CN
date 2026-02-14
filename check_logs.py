#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查日志中的prompt长度"""

import re

def main():
    try:
        with open('logs/tradingagents.log', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 查找所有关于prompt长度的日志
        pattern = r'构建完整请求prompt.*长度.*(\d+)'
        matches = re.findall(pattern, content)
        
        if matches:
            print(f"Found {len(matches)} log entries about prompt length:")
            for i, length in enumerate(matches[-10:], 1):  # 只显示最后10个
                print(f"  {i}. Prompt length: {length}")
        else:
            print("No log entries found about prompt length")
        
        # 查找关于提取prompt的日志
        pattern2 = r'提取prompt.*market_request_prompt'
        matches2 = re.findall(pattern2, content)
        if matches2:
            print(f"\nFound {len(matches2)} log entries about extracting market_request_prompt")
        else:
            print("\nNo log entries found about extracting market_request_prompt")
            
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
