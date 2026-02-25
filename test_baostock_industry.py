"""测试baostock行业数据"""
import baostock as bs

print("测试baostock行业数据接口")
print("="*60)

# 登录
lg = bs.login()
print(f"登录: {lg.error_code} - {lg.error_msg}")

# 测试获取行业板块列表
print("\n1. 获取行业分类")
rs = bs.query_industry_classify()
if rs:
    count = 0
    industries = []
    while rs.error_code == '0' and rs.next():
        data = rs.get_row_data()
        industries.append(data)
        if count < 10:
            print(f"行业: {data}")
        count += 1
    print(f"\n行业总数: {count}")
    
    # 找白酒行业
    for ind in industries:
        if ind and '白酒' in str(ind):
            print(f"白酒相关: {ind}")
else:
    print("获取行业分类失败")

# 测试获取行业K线
print("\n2. 获取白酒板块K线数据")
rs = bs.query_history_k_data_plus(
    "sz.399997",  # 假设这是中证白酒指数
    "date,open,high,low,close,volume",
    start_date="2026-02-20",
    end_date="2026-02-24",
    frequency="d"
)
if rs:
    count = 0
    while rs.error_code == '0' and rs.next():
        data = rs.get_row_data()
        print(f"K线: {data}")
        count += 1
        if count >= 5:
            break
    print(f"共获取 {count} 条")
else:
    print("获取K线失败")

# 登出
bs.logout()
