"""
东方财富股吧数据源适配器
用于获取A股股票的社交媒体信息（股吧热门帖子）
"""

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import DataSourceAdapter

logger = logging.getLogger("data_sources.eastmoney_adapter")


class EastMoneyAdapter(DataSourceAdapter):
    """东方财富股吧数据源适配器"""
    
    def __init__(self):
        super().__init__()
        self._name = "eastmoney"
        self._priority = 1
    
    @property
    def name(self) -> str:
        """数据源名称"""
        return self._name
    
    def _get_default_priority(self) -> int:
        """获取默认优先级"""
        return 1
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        try:
            import requests
            response = requests.get("https://guba.eastmoney.com", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_stock_list(self) -> Optional[pd.DataFrame]:
        """获取股票列表（不适用）"""
        return None
    
    def get_daily_basic(self, trade_date: str) -> Optional[pd.DataFrame]:
        """获取每日基础财务数据（不适用）"""
        return None
    
    def find_latest_trade_date(self) -> Optional[str]:
        """查找最新交易日期（不适用）"""
        return None
    
    def get_realtime_quotes(self) -> Optional[Dict[str, Dict[str, Optional[float]]]]:
        """获取实时行情（不适用）"""
        return None
    
    def get_kline(self, code: str, period: str = "day", limit: int = 120, adj: Optional[str] = None):
        """获取K线（不适用）"""
        return None
    
    def get_news(self, code: str, days: int = 7, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        获取东方财富股吧热门帖子
        
        Args:
            code: 股票代码
            days: 获取天数
            limit: 获取数量限制
            
        Returns:
            格式化的新闻数据列表，如果失败返回 None
        """
        try:
            import requests
            
            url = "https://guba.eastmoney.com/api"
            params = {
                "code": code,
                "count": limit,
                "page": 1
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.0 Safari/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and "data" in data and "list" in data["data"]:
                    posts = data["data"]["list"]
                    
                    formatted_posts = []
                    for post in posts[:limit]:
                        formatted_post = {
                            "title": post.get("title", ""),
                            "content": post.get("content", "")[:200],
                            "author": post.get("nickname", post.get("author", "")),
                            "publish_time": self._format_time(post.get("create_time", "")),
                            "likes": post.get("agree", 0),
                            "comments": post.get("reply", 0),
                            "sentiment": self._analyze_sentiment(post.get("content", "")),
                            "source": "东方财富股吧"
                        }
                        formatted_posts.append(formatted_post)
                    
                    logger.info(f"✅ 东方财富股吧获取成功: {code}, 获取 {len(formatted_posts)} 条帖子")
                    return formatted_posts
                else:
                    logger.warning(f"⚠️ 东方财富股吧返回数据格式异常: {code}")
                    return None
            else:
                logger.warning(f"⚠️ 东方财富股吧请求失败: {code}, 状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 东方财富股吧获取失败: {code}, 错误: {e}")
            return None
    
    def _format_time(self, time_str: str) -> str:
        """格式化时间字符串"""
        try:
            if not time_str:
                return ""
            
            if "分钟前" in time_str:
                return time_str
            elif "小时前" in time_str:
                return time_str
            elif "今天" in time_str:
                return datetime.now().strftime("%Y-%m-%d")
            else:
                return time_str
        except:
            return time_str
    
    def _analyze_sentiment(self, content: str) -> str:
        """简单分析情绪倾向"""
        if not content:
            return "中性"
        
        positive_keywords = ["涨", "好", "强", "买入", "看多", "突破", "上涨", "利好"]
        negative_keywords = ["跌", "坏", "弱", "卖出", "看空", "跌破", "下跌", "利空"]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in content)
        negative_count = sum(1 for keyword in negative_keywords if keyword in content)
        
        if positive_count > negative_count:
            return "积极"
        elif negative_count > positive_count:
            return "消极"
        else:
            return "中性"
    
    def get_stock_list(self) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表（不支持，返回None）"""
        return None
    
    def get_daily_basic(self, trade_date: str) -> Optional[List[Dict[str, Any]]]:
        """获取每日基础数据（不支持，返回None）"""
        return None
    
    def find_latest_trade_date(self) -> Optional[str]:
        """查找最新交易日期（不支持，返回None）"""
        return None
    
    def get_realtime_quotes(self) -> Optional[List[Dict[str, Any]]]:
        """获取实时行情（不支持，返回None）"""
        return None
    
    def get_kline(self, code: str, period: str = "day", limit: int = 100, adj: bool = True) -> Optional[List[Dict[str, Any]]]:
        """获取K线数据（不支持，返回None）"""
        return None
