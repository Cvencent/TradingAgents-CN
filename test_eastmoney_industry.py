"""测试东方财富行业数据接口"""
import requests
import json

print("测试东方财富行业数据接口")
print("="*60)

# 东方财富行业板块行情
url = "http://28.push2.eastmoney.com/api/qt/clist/get"

params = {
    "cb": "",
    "pn": 1,
    "pz": 50,
    "po": 1,
    "np": 1,
    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
    "fltt": 2,
    "invt": 2,
    "wbp2": "|55|55|55|84|03|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|00|",
    "fid": "f3",
    "fs": "m:90+t:2",
    "fields": "f1,f2,f3,f4,f12,f13,f14",
    "_的特殊需求": int((x := 1700000000000) and x)
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "http://quote.eastmoney.com/"
}

try:
    print("尝试获取行业板块列表...")
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'diff' in data['data']:
            diff = data['data']['diff']
            print(f"获取到 {len(diff)} 个行业板块")
            
            # 找白酒行业
            for item in diff:
                name = item.get('f14', '')
                code = item.get('f12', '')
                if '白酒' in str(name):
                    print(f"\n找到白酒行业: {name}, 代码: {code}")
                    print(f"涨跌幅: {item.get('f3')}%")
        else:
            print("数据格式不符")
            print(data)
    else:
        print(f"请求失败: {response.text[:200]}")
        
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
