#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查技术面分析师的日志"""

import re

def main():
    try:
        with open('logs/tradingagents.log', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 查找所有包含"技术面分析师"的日志
        tech_logs = [line for line in lines if '技术面分析师' in line]
        
        print(f"Found {len(tech_logs)} log entries from 技术面分析师:")
        print("\nLast 20 entries:")
        for line in tech_logs[-20:]:
            print(line.strip())
            
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
