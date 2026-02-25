"""直接测试akshare行业走势接口"""
import akshare as ak
import time

industry_name = "白酒Ⅱ"

print(f"测试行业: {industry_name}")
print("="*60)

# 第一次尝试
print("\n第1次尝试...")
try:
    board = ak.stock_board_industry_name_em()
    print(f"行业板块列表获取成功: {len(board)} 条")
    
    row = board[board['名称'] == industry_name]
    if not row.empty:
        code = row.iloc[0]['板块代码']
        print(f"行业代码: {code}")
        
        time.sleep(1)
        
        hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20260224", end_date="20260224", adjust="")
        print(f"行业走势数据: {len(hist) if hist is not None else 0} 条")
        if hist is not None and not hist.empty:
            print(hist)
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")

# 第二次尝试
print("\n第2次尝试...")
time.sleep(2)
try:
    board = ak.stock_board_industry_name_em()
    print(f"行业板块列表获取成功: {len(board)} 条")
    
    row = board[board['名称'] == industry_name]
    if not row.empty:
        code = row.iloc[0]['板块代码']
        print(f"行业代码: {code}")
        
        time.sleep(1)
        
        hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20260224", end_date="20260224", adjust="")
        print(f"行业走势数据: {len(hist) if hist is not None else 0} 条")
        if hist is not None and not hist.empty:
            print(hist)
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")

# 第三次尝试
print("\n第3次尝试...")
time.sleep(2)
try:
    board = ak.stock_board_industry_name_em()
    print(f"行业板块列表获取成功: {len(board)} 条")
    
    row = board[board['名称'] == industry_name]
    if not row.empty:
        code = row.iloc[0]['板块代码']
        print(f"行业代码: {code}")
        
        time.sleep(1)
        
        hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20260224", end_date="20260224", adjust="")
        print(f"行业走势数据: {len(hist) if hist is not None else 0} 条")
        if hist is not None and not hist.empty:
            print(hist)
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
