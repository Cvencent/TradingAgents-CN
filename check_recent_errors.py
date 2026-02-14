#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查最近的错误日志"""

import re

def main():
    try:
        with open('logs/tradingagents.log', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 查找所有包含"ERROR"或"error"的日志
        error_logs = []
        for line in lines:
            if 'ERROR' in line or 'error' in line.lower() or '失败' in line or 'failed' in line.lower():
                error_logs.append(line.strip())
        
        print(f"Found {len(error_logs)} error log entries:")
        print("\nLast 30 entries:")
        for line in error_logs[-30:]:
            print(line)
            
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
