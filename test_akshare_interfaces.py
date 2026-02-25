"""测试akshare其他行业数据接口"""
import akshare as ak
import time

print("测试不同的akshare行业数据接口")
print("="*60)

# 测试1: stock_board_industry_name_em
print("\n1. stock_board_industry_name_em()")
try:
    time.sleep(1)
    board = ak.stock_board_industry_name_em()
    print(f"成功: {len(board)} 条行业")
    print(board.head(3))
except Exception as e:
    print(f"失败: {e}")

# 测试2: stock_board_industry_cons_em
print("\n2. stock_board_industry_cons_em()")
try:
    time.sleep(1)
    cons = ak.stock_board_industry_cons_em(symbol="白酒Ⅱ")
    print(f"成功: {len(cons)} 只股票")
except Exception as e:
    print(f"失败: {e}")

# 测试3: stock_board_industry_sina
print("\n3. stock_board_industry_sina()")
try:
    time.sleep(1)
    sina = ak.stock_board_industry_sina()
    print(f"成功: {len(sina)} 条行业")
except Exception as e:
    print(f"失败: {e}")

# 测试4: stock_board_industry_ths
print("\n4. stock_board_industry_ths()")
try:
    time.sleep(1)
    ths = ak.stock_board_industry_ths()
    print(f"成功: {len(ths)} 条行业")
except Exception as e:
    print(f"失败: {e}")

# 测试5: stock_sse_minute - 测试是否所有接口都有问题
print("\n5. 测试上证指数分钟数据 (stock_sse_minute_spot)")
try:
    time.sleep(1)
    spot = ak.stock_sse_minute_spot(symbol="000001", period="1", adjust="qfq")
    print(f"成功: {len(spot)} 条")
except Exception as e:
    print(f"失败: {e}")

print("\n结论: 如果所有接口都失败，说明是网络问题或akshare被限制")
