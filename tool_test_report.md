# 工具测试报告模板

**创建时间**: 2026-02-03
**说明**: 请启动服务器后运行 `python test_tools.py` 生成完整测试报告

---

## 测试股票列表

| 股票代码 | 名称 | 市场 |
|---------|------|------|
| 000001 | 平安银行 | A股 |
| 0700.HK | 腾讯控股 | 港股 |
| AAPL | 苹果公司 | 美股 |

---

## 工具列表

| 工具名称 | 用途 | 对应分析师 |
|---------|------|-----------|
| get_china_stock_info_unified | 获取A股股票基本信息 | 中国市场分析师 |
| get_stock_fundamentals_unified | 获取统一基本面数据 | 基本面分析师 |
| get_stock_market_data_unified | 获取统一市场数据 | 技术面分析师 |
| get_stock_news_unified | 获取统一新闻数据 | 新闻分析师 |
| get_stock_sentiment_unified | 获取统一情绪数据 | 社交媒体分析师 |
| get_google_news | 获取Google新闻 | 新闻分析师 |
| get_stock_money_flow_unified | 获取资金流向数据 | 资金面分析师 |
| get_stock_market_trend_unified | 获取市场趋势数据 | 市场趋势分析师 |

---

## 工具详细说明

### 1. get_china_stock_info_unified
- **用途**: 获取中国A股股票的基本信息
- **参数**: ticker (股票代码)
- **返回**: 股票名称、行业、市值等基本信息
- **数据源**: Tushare / AKShare / BaoStock

### 2. get_stock_fundamentals_unified
- **用途**: 获取股票基本面数据
- **参数**: ticker, start_date, end_date, curr_date
- **返回**: 财务数据、估值指标等
- **数据源**: Tushare / AKShare / Alpha Vantage / Finnhub

### 3. get_stock_market_data_unified
- **用途**: 获取股票市场数据（价格、成交量等）
- **参数**: ticker, start_date, end_date
- **返回**: OHLCV数据、技术指标
- **数据源**: Tushare / AKShare / yfinance

### 4. get_stock_news_unified
- **用途**: 获取股票相关新闻
- **参数**: stock_code, max_news
- **返回**: 新闻标题、摘要、来源
- **数据源**: Google News / Finnhub / 东方财富

### 5. get_stock_sentiment_unified
- **用途**: 获取社交媒体情绪数据
- **参数**: stock_code
- **返回**: 情绪分析结果
- **数据源**: Reddit / Twitter / 股吧

### 6. get_google_news
- **用途**: 获取Google新闻
- **参数**: query, curr_date, look_back_days
- **返回**: 新闻列表
- **数据源**: Google News API

### 7. get_stock_money_flow_unified
- **用途**: 获取资金流向数据
- **参数**: ticker, days
- **返回**: 主力资金、散户资金流向
- **数据源**: Tushare / AKShare

### 8. get_stock_market_trend_unified
- **用途**: 获取市场趋势数据
- **参数**: ticker, start_date, end_date
- **返回**: 市场趋势分析
- **数据源**: 内部计算

---

## 测试方法

### 1. 启动后端服务器
```bash
cd D:\trade\TradingAgents-CN
python -m app.main
```

### 2. 运行测试脚本
```bash
python test_tools.py
```

### 3. 查看报告
打开生成的 `tool_test_report.md` 文件查看测试结果

---

## 常见问题

### 1. 数据源不可用
- 检查 `.env` 文件中的API密钥配置
- 确认MongoDB连接正常
- 检查网络连接

### 2. Unicode编码错误
- Windows控制台可能不支持某些Unicode字符
- 建议使用VS Code终端或PowerShell运行

### 3. 测试超时
- 部分工具需要从外部API获取数据
- 可能会比较耗时，请耐心等待

---

## 数据源配置

在 `.env` 文件中配置以下API密钥：

```env
# Tushare (A股数据)
TUSHARE_API_KEY=your_tushare_api_key

# Finnhub (美股数据)
FINNHUB_API_KEY=your_finnhub_api_key

# Alpha Vantage
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key

# DashScope (阿里云)
DASHSCOPE_API_KEY=your_dashscope_api_key
```

---

## 测试结果记录

| 股票 | 工具 | 状态 | 结果 |
|------|------|------|------|
| 000001 | get_china_stock_info_unified | 待测试 | - |
| 000001 | get_stock_fundamentals_unified | 待测试 | - |
| 000001 | get_stock_market_data_unified | 待测试 | - |
| 000001 | get_stock_news_unified | 待测试 | - |
| 000001 | get_stock_sentiment_unified | 待测试 | - |
| 000001 | get_stock_money_flow_unified | 待测试 | - |
| 0700.HK | get_stock_fundamentals_unified | 待测试 | - |
| 0700.HK | get_stock_market_data_unified | 待测试 | - |
| 0700.HK | get_stock_news_unified | 待测试 | - |
| AAPL | get_stock_fundamentals_unified | 待测试 | - |
| AAPL | get_stock_market_data_unified | 待测试 | - |
| AAPL | get_stock_news_unified | 待测试 | - |
