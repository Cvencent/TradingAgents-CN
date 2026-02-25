"""调试行业信息获取"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import akshare as ak

ticker = "600519.SH"
stock_code = ticker.replace('.SH', '').replace('.SZ', '')

print(f"股票代码: {stock_code}")
print("="*60)

# 获取股票详细信息
stock_info_detail = ak.stock_individual_info_em(symbol=stock_code)

print(f"返回类型: {type(stock_info_detail)}")
print(f"是否为None: {stock_info_detail is None}")
print(f"是否为空: {stock_info_detail.empty if stock_info_detail is not None else 'N/A'}")
print()

if stock_info_detail is not None and not stock_info_detail.empty:
    print("数据内容:")
    print(stock_info_detail)
    print()
    
    # 提取股票名称
    name_row = stock_info_detail[stock_info_detail['item'] == '股票简称']
    print(f"股票简称查询结果: {name_row}")
    if not name_row.empty:
        stock_name = name_row['value'].iloc[0]
        print(f"股票名称: {stock_name}")
    
    # 提取行业信息
    industry_row = stock_info_detail[stock_info_detail['item'] == '所属行业']
    print(f"所属行业查询结果: {industry_row}")
    if not industry_row.empty:
        industry_name = industry_row['value'].iloc[0]
        print(f"所属行业: {industry_name}")
