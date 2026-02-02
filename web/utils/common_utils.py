"""
通用工具函数
"""

from datetime import datetime, timedelta, timezone


def get_china_time() -> datetime:
    """
    获取中国时区（UTC+8）的当前时间
    
    Returns:
        datetime: 带时区信息的中国时间
    """
    china_tz = timezone(timedelta(hours=8))
    return datetime.now(china_tz)


def get_china_time_str(fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    获取中国时区（UTC+8）的当前时间字符串
    
    Args:
        fmt: 时间格式字符串，默认 '%Y-%m-%d %H:%M:%S'
    
    Returns:
        str: 格式化后的中国时间字符串
    """
    return get_china_time().strftime(fmt)
