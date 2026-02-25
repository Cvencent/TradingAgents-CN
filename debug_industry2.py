"""测试行业走势"""
import sys
import os
import pandas as pd
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import akshare as ak

industry_name = "白酒Ⅱ"
start_date = "2026-02-24"
end_date = "2026-02-24"

print(f"行业名称: {industry_name}")
print("="*60)

# 重试机制
for attempt in range(3):
    try:
        print(f"尝试 {attempt + 1}/3...")
        
        # 获取同花顺行业代码
        industry_board = ak.stock_board_industry_name_em()
        print(f"行业板块数据: {len(industry_board)} 条")
        
        industry_row_data = industry_board[industry_board['名称'] == industry_name]
        print(f"匹配结果: {len(industry_row_data)} 条")
        
        if not industry_row_data.empty:
            industry_code = industry_row_data.iloc[0]['板块代码']
            print(f"行业代码: {industry_code}")
            
            time.sleep(1)  # 等待一下
            
            # 获取行业日K线数据
            industry_daily = ak.stock_zh_a_hist(
                symbol=industry_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            print(f"行业日K数据: {len(industry_daily) if industry_daily is not None else 0} 条")
            
            if industry_daily is not None and not industry_daily.empty:
                print("数据内容:")
                print(industry_daily)
                break
            
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        time.sleep(2)
