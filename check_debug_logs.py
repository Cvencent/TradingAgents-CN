#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查调试日志"""

import re

def main():
    try:
        with open('logs/tradingagents.log', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 查找所有PROMPTS DEBUG日志
        pattern = r'PROMPTS DEBUG.*'
        matches = re.findall(pattern, content)
        
        print(f"Found {len(matches)} PROMPTS DEBUG log entries:")
        for match in matches[-20:]:  # 只显示最后20个
            print(f"  {match}")
            
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
