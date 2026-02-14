"""
分析报告管理API路由
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .auth_db import get_current_user
from ..core.database import get_mongo_db
from ..utils.timezone import to_config_tz
import logging

logger = logging.getLogger("webapi")

# 股票名称缓存
_stock_name_cache = {}

def _build_report_query(report_id: str) -> dict:
    """构建报告查询条件 - 支持多种ID格式

    Args:
        report_id: 报告ID (可以是task_id, analysis_id, 或MongoDB _id)

    Returns:
        MongoDB查询条件字典
    """
    from bson import ObjectId
    # 尝试多种ID格式
    query_conditions = [
        {"task_id": report_id},
        {"analysis_id": report_id},
    ]

    # 尝试ObjectId格式（24位十六进制字符串）
    if len(report_id) == 24:
        try:
            query_conditions.append({"_id": ObjectId(report_id)})
        except Exception:
            pass

    return {"$or": query_conditions}


def get_stock_name(stock_code: str) -> str:
    """
    获取股票名称
    优先级：缓存 -> MongoDB（按数据源优先级） -> 默认返回股票代码
    """
    global _stock_name_cache

    # 检查缓存
    if stock_code in _stock_name_cache:
        return _stock_name_cache[stock_code]

    try:
        # 从 MongoDB 获取股票名称
        from ..core.database import get_mongo_db_sync
        from ..core.unified_config import UnifiedConfigManager

        db = get_mongo_db_sync()
        code6 = str(stock_code).zfill(6)

        # 🔥 按数据源优先级查询
        config = UnifiedConfigManager()
        data_source_configs = config.get_data_source_configs()

        # 提取启用的数据源，按优先级排序
        enabled_sources = [
            ds.type.lower() for ds in data_source_configs
            if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock']
        ]

        if not enabled_sources:
            enabled_sources = ['tushare', 'akshare', 'baostock']

        # 按数据源优先级查询
        stock_info = None
        for data_source in enabled_sources:
            stock_info = db.stock_basic_info.find_one(
                {"$or": [{"symbol": code6}, {"code": code6}], "source": data_source}
            )
            if stock_info:
                logger.debug(f"✅ 使用数据源 {data_source} 获取股票名称 {code6}")
                break

        # 如果所有数据源都没有，尝试不带 source 条件查询（兼容旧数据）
        if not stock_info:
            stock_info = db.stock_basic_info.find_one(
                {"$or": [{"symbol": code6}, {"code": code6}]}
            )
            if stock_info:
                logger.warning(f"⚠️ 使用旧数据（无 source 字段）获取股票名称 {code6}")

        if stock_info and stock_info.get("name"):
            stock_name = stock_info["name"]
            _stock_name_cache[stock_code] = stock_name
            return stock_name

        # 如果没有找到，返回股票代码
        _stock_name_cache[stock_code] = stock_code
        return stock_code

    except Exception as e:
        logger.warning(f"⚠️ 获取股票名称失败 {stock_code}: {e}")
        return stock_code


# 统一构建报告查询：支持 _id(ObjectId) / analysis_id / task_id 三种
def _build_report_query(report_id: str) -> Dict[str, Any]:
    ors = [
        {"analysis_id": report_id},
        {"task_id": report_id},
    ]
    try:
        from bson import ObjectId
        ors.append({"_id": ObjectId(report_id)})
    except Exception:
        pass
    return {"$or": ors}

router = APIRouter(prefix="/api/reports", tags=["reports"])

class ReportFilter(BaseModel):
    """报告筛选参数"""
    search_keyword: Optional[str] = None
    market_filter: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    stock_code: Optional[str] = None
    report_type: Optional[str] = None

class ReportListResponse(BaseModel):
    """报告列表响应"""
    reports: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int

@router.get("/list", response_model=Dict[str, Any])
async def get_reports_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search_keyword: Optional[str] = Query(None, description="搜索关键词"),
    market_filter: Optional[str] = Query(None, description="市场筛选（A股/港股/美股）"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    user: dict = Depends(get_current_user)
):
    """获取分析报告列表"""
    try:
        logger.info(f"🔍 获取报告列表: 用户={user['id']}, 页码={page}, 每页={page_size}, 市场={market_filter}")

        db = get_mongo_db()

        # 构建查询条件
        query = {}

        # 搜索关键词
        if search_keyword:
            query["$or"] = [
                {"stock_symbol": {"$regex": search_keyword, "$options": "i"}},
                {"analysis_id": {"$regex": search_keyword, "$options": "i"}},
                {"summary": {"$regex": search_keyword, "$options": "i"}}
            ]

        # 市场筛选
        if market_filter:
            query["market_type"] = market_filter

        # 股票代码筛选
        if stock_code:
            query["stock_symbol"] = stock_code

        # 日期范围筛选
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["analysis_date"] = date_query

        logger.info(f"📊 查询条件: {query}")

        # 计算总数
        total = await db.analysis_reports.count_documents(query)

        # 分页查询
        skip = (page - 1) * page_size
        cursor = db.analysis_reports.find(query).sort("created_at", -1).skip(skip).limit(page_size)

        reports = []
        async for doc in cursor:
            # 转换为前端需要的格式
            stock_code = doc.get("stock_symbol", "")
            # 🔥 优先使用MongoDB中保存的股票名称，如果没有则查询
            stock_name = doc.get("stock_name")
            if not stock_name:
                stock_name = get_stock_name(stock_code)

            # 🔥 获取市场类型，如果没有则根据股票代码推断
            market_type = doc.get("market_type")
            if not market_type:
                from tradingagents.utils.stock_utils import StockUtils
                market_info = StockUtils.get_market_info(stock_code)
                market_type_map = {
                    "china_a": "A股",
                    "hong_kong": "港股",
                    "us": "美股",
                    "unknown": "A股"
                }
                market_type = market_type_map.get(market_info.get("market", "unknown"), "A股")

            # 获取创建时间（数据库中是 UTC 时间，需要转换为 UTC+8）
            created_at = doc.get("created_at", datetime.utcnow())
            created_at_tz = to_config_tz(created_at)  # 转换为 UTC+8 并添加时区信息

            report = {
                "id": str(doc["_id"]),
                "analysis_id": doc.get("analysis_id", ""),
                "title": f"{stock_name}({stock_code}) 分析报告",
                "stock_code": stock_code,
                "stock_name": stock_name,
                "market_type": market_type,  # 🔥 添加市场类型字段
                "model_info": doc.get("model_info", "Unknown"),  # 🔥 添加模型信息字段
                "type": "single",  # 目前主要是单股分析
                "format": "markdown",  # 主要格式
                "status": doc.get("status", "completed"),
                "created_at": created_at_tz.isoformat() if created_at_tz else str(created_at),
                "analysis_date": doc.get("analysis_date", ""),
                "analysts": doc.get("analysts", []),
                "research_depth": doc.get("research_depth", 1),
                "summary": doc.get("summary", ""),
                "file_size": len(str(doc.get("reports", {}))),  # 估算大小
                "source": doc.get("source", "unknown"),
                "task_id": doc.get("task_id", "")
            }
            reports.append(report)

        logger.info(f"✅ 查询完成: 总数={total}, 返回={len(reports)}")

        return {
            "success": True,
            "data": {
                "reports": reports,
                "total": total,
                "page": page,
                "page_size": page_size
            },
            "message": "报告列表获取成功"
        }

    except Exception as e:
        logger.error(f"[X] 获取报告列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/detail")
async def get_report_detail(
    report_id: str,
    user: dict = Depends(get_current_user)
):
    """获取报告详情"""
    try:
        logger.info(f"🔍 获取报告详情: {report_id}")

        db = get_mongo_db()

        # 支持 ObjectId / analysis_id / task_id
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            # 兜底：从 analysis_tasks.result 中还原报告详情
            logger.info(f"⚠️ 未在analysis_reports找到，尝试从analysis_tasks还原: {report_id}")
            tasks_doc = await db.analysis_tasks.find_one(
                {"$or": [{"task_id": report_id}, {"result.analysis_id": report_id}]},
                {"result": 1, "task_id": 1, "stock_code": 1, "created_at": 1, "completed_at": 1}
            )
            if not tasks_doc or not tasks_doc.get("result"):
                raise HTTPException(status_code=404, detail="报告不存在")

            r = tasks_doc["result"] or {}
            created_at = tasks_doc.get("created_at")
            updated_at = tasks_doc.get("completed_at") or created_at

            # 转换时区：数据库中是 UTC 时间，转换为 UTC+8
            created_at_tz = to_config_tz(created_at)
            updated_at_tz = to_config_tz(updated_at)

            def to_iso(x):
                if hasattr(x, "isoformat"):
                    return x.isoformat()
                return x or ""

            stock_symbol = r.get("stock_symbol", r.get("stock_code", tasks_doc.get("stock_code", "")))
            stock_name = r.get("stock_name")
            if not stock_name:
                stock_name = get_stock_name(stock_symbol)

            report = {
                "id": tasks_doc.get("task_id", report_id),
                "analysis_id": r.get("analysis_id", ""),
                "stock_symbol": stock_symbol,
                "stock_name": stock_name,  # 🔥 添加股票名称字段
                "model_info": r.get("model_info", "Unknown"),  # 🔥 添加模型信息字段
                "analysis_date": r.get("analysis_date", ""),
                "status": r.get("status", "completed"),
                "created_at": to_iso(created_at_tz),
                "updated_at": to_iso(updated_at_tz),
                "analysts": r.get("analysts", []),
                "research_depth": r.get("research_depth", 1),
                "summary": r.get("summary", ""),
                "reports": r.get("reports", {}),
                "source": "analysis_tasks",
                "task_id": tasks_doc.get("task_id", report_id),
                "recommendation": r.get("recommendation", ""),
                "confidence_score": r.get("confidence_score", 0.0),
                "risk_level": r.get("risk_level", "中等"),
                "key_points": r.get("key_points", []),
                "execution_time": r.get("execution_time", 0),
                "tokens_used": r.get("tokens_used", 0)
            }
        else:
            # 转换为详细格式（analysis_reports 命中）
            stock_symbol = doc.get("stock_symbol", "")
            stock_name = doc.get("stock_name")
            if not stock_name:
                stock_name = get_stock_name(stock_symbol)

            # 获取时间（数据库中是 UTC 时间，需要转换为 UTC+8）
            created_at = doc.get("created_at", datetime.utcnow())
            updated_at = doc.get("updated_at", datetime.utcnow())

            # 转换时区：数据库中是 UTC 时间，转换为 UTC+8
            created_at_tz = to_config_tz(created_at)
            updated_at_tz = to_config_tz(updated_at)

            report = {
                "id": str(doc["_id"]),
                "analysis_id": doc.get("analysis_id", ""),
                "stock_symbol": stock_symbol,
                "stock_name": stock_name,  # 🔥 添加股票名称字段
                "model_info": doc.get("model_info", "Unknown"),  # 🔥 添加模型信息字段
                "analysis_date": doc.get("analysis_date", ""),
                "status": doc.get("status", "completed"),
                "created_at": created_at_tz.isoformat() if created_at_tz else str(created_at),
                "updated_at": updated_at_tz.isoformat() if updated_at_tz else str(updated_at),
                "analysts": doc.get("analysts", []),
                "research_depth": doc.get("research_depth", 1),
                "summary": doc.get("summary", ""),
                "reports": doc.get("reports", {}),
                "source": doc.get("source", "unknown"),
                "task_id": doc.get("task_id", ""),
                "recommendation": doc.get("recommendation", ""),
                "confidence_score": doc.get("confidence_score", 0.0),
                "risk_level": doc.get("risk_level", "中等"),
                "key_points": doc.get("key_points", []),
                "execution_time": doc.get("execution_time", 0),
                "tokens_used": doc.get("tokens_used", 0)
            }

        return {
            "success": True,
            "data": report,
            "message": "报告详情获取成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[X] 获取报告详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/content/{module}")
async def get_report_module_content(
    report_id: str,
    module: str,
    user: dict = Depends(get_current_user)
):
    """获取报告特定模块的内容"""
    try:
        logger.info(f"🔍 获取报告模块内容: {report_id}/{module}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="报告不存在")

        reports = doc.get("reports", {})

        if module not in reports:
            raise HTTPException(status_code=404, detail=f"模块 {module} 不存在")

        content = reports[module]

        return {
            "success": True,
            "data": {
                "module": module,
                "content": content,
                "content_type": "markdown" if isinstance(content, str) else "json"
            },
            "message": "模块内容获取成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[X] 获取报告模块内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: dict = Depends(get_current_user)
):
    """删除报告"""
    try:
        logger.info(f"🗑️ 删除报告: {report_id}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        result = await db.analysis_reports.delete_one(query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="报告不存在")

        logger.info(f"✅ 报告删除成功: {report_id}")

        return {
            "success": True,
            "message": "报告删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[X] 删除报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/prompts")
async def get_analysis_prompts(
    report_id: str,
    user: dict = Depends(get_current_user)
):
    """获取分析过程中使用的prompt

    从MongoDB的analysis_reports集合中提取各分析师使用的prompt
    按分析步骤分组返回（与报告详情页面步骤一致）
    """
    try:
        logger.info(f"🔍 获取分析prompt: {report_id}")

        db = get_mongo_db()

        # 查询报告
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            # 从analysis_tasks查找
            task_doc = await db.analysis_tasks.find_one(
                {"$or": [
                    {"task_id": report_id},
                    {"result.analysis_id": report_id}
                ]},
                {"task_id": 1, "stock_code": 1, "result.prompts": 1}
            )
            if not task_doc:
                raise HTTPException(status_code=404, detail="报告不存在")

            result = task_doc.get("result", {})
            prompts_dict = result.get("prompts", {})

            if not prompts_dict:
                return {
                    "success": True,
                    "data": {
                        "task_id": task_doc.get("task_id"),
                        "prompts": [],
                        "prompts_by_step": {},
                        "count": 0,
                        "warning": "该分析任务的prompt数据未保存。messages数据在分析过程中未被记录到数据库。"
                    },
                    "message": "Prompt获取成功，但该任务未保存prompt数据"
                }

            prompts = []
            for analyst, content in prompts_dict.items():
                prompts.append({
                    "analyst": analyst,
                    "analyst_name": analyst.replace("_", " ").title(),
                    "type": "stored",
                    "content": content[:5000] if isinstance(content, str) else str(content)[:5000],
                    "timestamp": ""
                })

            return {
                "success": True,
                "data": {
                    "task_id": task_doc.get("task_id"),
                    "prompts": prompts,
                    "prompts_by_step": {},
                    "count": len(prompts)
                },
                "message": "Prompt获取成功"
            }

        # 🔥 按分析步骤组织prompts（与报告详情页面一致）
        def organize_prompts_by_step(prompts_list):
            """将prompts按分析步骤分组（与报告详情页面一致）"""
            # 分析步骤定义（与报告详情页面一致）
            step_definitions = [
                {
                    "key": "analyst_team",
                    "name": "📊 分析师团队",
                    "icon": "📊",
                    "analysts": ["market_report", "sentiment_report", "news_report", "fundamentals_report", "capital_flow_report"]
                },
                {
                    "key": "research_team",
                    "name": "🔬 研究团队",
                    "icon": "🔬",
                    "analysts": ["bull_researcher", "bear_researcher", "research_team_decision"]
                },
                {
                    "key": "trading_team",
                    "name": "💼 交易团队",
                    "icon": "💼",
                    "analysts": ["trader_investment_plan"]
                },
                {
                    "key": "risk_team",
                    "name": "⚠️ 风险管理",
                    "icon": "⚠️",
                    "analysts": ["risky_analyst", "safe_analyst", "neutral_analyst", "risk_management_decision"]
                },
                {
                    "key": "final_decision",
                    "name": "🎯 最终决策",
                    "icon": "🎯",
                    "analysts": ["final_trade_decision"]
                },
            ]

            # 分析师中文名称映射（与报告详情页面一致）
            analyst_names = {
                "market_report": "技术面分析",
                "sentiment_report": "市场情绪分析",
                "news_report": "新闻事件分析",
                "fundamentals_report": "基本面分析",
                "capital_flow_report": "资金面分析",
                "bull_researcher": "多头研究员",
                "bear_researcher": "空头研究员",
                "research_team_decision": "研究经理决策",
                "trader_investment_plan": "交易员计划",
                "risky_analyst": "激进分析师",
                "safe_analyst": "保守分析师",
                "neutral_analyst": "中性分析师",
                "risk_management_decision": "投资组合经理",
                "final_trade_decision": "最终交易决策",
            }

            # 初始化步骤
            steps = {step["key"]: {
                "name": step["name"],
                "icon": step["icon"],
                "prompts": []
            } for step in step_definitions}

            # 将prompts分配到对应步骤
            for p in prompts_list:
                analyst = p.get("analyst", "")
                content = p.get("content", "")
                analyst_name = p.get("analyst_name", analyst_names.get(analyst, analyst))

                # 查找该分析师属于哪个步骤
                assigned = False
                for step in step_definitions:
                    if analyst in step["analysts"]:
                        steps[step["key"]]["prompts"].append({
                            "analyst": analyst,
                            "analyst_name": analyst_name,
                            "content": content,
                            "type": p.get("type", "unknown")
                        })
                        assigned = True
                        break

                # 如果没找到对应的步骤，尝试模糊匹配
                if not assigned:
                    for step in step_definitions:
                        for step_analyst in step["analysts"]:
                            if analyst.startswith(step_analyst.split("_")[0]):
                                steps[step["key"]]["prompts"].append({
                                    "analyst": analyst,
                                    "analyst_name": analyst_name,
                                    "content": content,
                                    "type": p.get("type", "unknown")
                                })
                                assigned = True
                                break
                        if assigned:
                            break

            # 移除空的步骤
            return {k: v for k, v in steps.items() if v["prompts"]}

        # 🔥 优先从prompts字段获取（这是保存的原始request_prompt）
        prompts_dict = doc.get("prompts", {})
        if prompts_dict:
            logger.info(f"📝 从prompts字段获取原始request_prompts，共 {len(prompts_dict)} 个")
            prompts = []
            for analyst, content in prompts_dict.items():
                prompts.append({
                    "analyst": analyst,
                    "analyst_name": analyst.replace("_", " ").title(),
                    "type": "original",
                    "content": content[:5000] if isinstance(content, str) else str(content)[:5000],
                    "timestamp": ""
                })

            prompts_by_step = organize_prompts_by_step(prompts)
            logger.info(f"✅ 从prompts字段找到 {len(prompts)} 个原始prompt")

            return {
                "success": True,
                "data": {
                    "task_id": doc.get("task_id") or report_id,
                    "prompts": prompts,
                    "prompts_by_step": prompts_by_step,
                    "count": len(prompts),
                    "source": "original_prompts"
                },
                "message": f"成功获取 {len(prompts)} 个原始request prompt"
            }

        # 如果没有prompts字段，尝试从messages中提取
        messages = doc.get("messages", [])
        if messages:
            logger.info(f"📝 从messages中提取prompts，共 {len(messages)} 条消息")

            analyst_mapping = {
                'market_report': 'Market Analyst',
                'fundamentals_report': 'Fundamentals Analyst',
                'sentiment_report': 'Sentiment Analyst',
                'news_report': 'News Analyst',
                'bull_researcher': 'Bull Researcher',
                'bear_researcher': 'Bear Researcher',
                'risky_analyst': 'Risky Analyst',
                'safe_analyst': 'Safe Analyst',
                'neutral_analyst': 'Neutral Analyst',
                'investment_plan': 'Research Team',
                'trader_investment_plan': 'Trader',
                'final_trade_decision': 'Final Decision',
            }

            # 🔥 关键修复：从消息内容中识别分析师的关键词映射
            analyst_keywords = {
                'market_report': ['market analyst', '市场分析师', '技术面分析', '技术分析师', '股票趋势分析', '市场趋势', '股票市场趋势'],
                'fundamentals_report': ['fundamentals analyst', '基本面分析师', '基本面分析', '公司基本信息'],
                'sentiment_report': ['sentiment analyst', '情绪分析师', '市场情绪分析', 'sentiment'],
                'news_report': ['news analyst', '新闻分析师', '新闻事件分析', '新闻舆情'],
                'bull_researcher': ['bull researcher', '多头研究员', 'bullish', '看涨', '牛市'],
                'bear_researcher': ['bear researcher', '空头研究员', 'bearish', '看跌', '熊市'],
                'risky_analyst': ['risky analyst', '激进分析师', '激进风险评估', '激进'],
                'safe_analyst': ['safe analyst', '保守分析师', '保守风险评估', '保守'],
                'neutral_analyst': ['neutral analyst', '中性分析师', '中性风险评估', '中性'],
                'trader_investment_plan': ['trader', '交易员', '交易计划', '投资策略'],
                'final_trade_decision': ['final decision', '最终决策', '最终交易决策', '投资建议', '卖出', '买入', '持有'],
            }

            prompts = []

            # 🔥 新策略：为每个分析师单独收集消息
            # 首先，找出所有涉及的分析师
            analyst_messages = {key: [] for key in analyst_mapping.keys()}

            for msg in messages:
                try:
                    msg_type = msg.get('type', '') if isinstance(msg, dict) else type(msg).__name__
                    msg_content = msg.get('content', '') if isinstance(msg, dict) else (msg.content if hasattr(msg, 'content') else str(msg))

                    if msg_type in ['system', 'System', 'system', 'remove', 'Remove']:
                        continue

                    if not msg_content:
                        continue

                    # 检查这条消息属于哪些分析师
                    content_lower = str(msg_content).lower()
                    matched_analysts = []
                    for analyst_key, keywords in analyst_keywords.items():
                        for keyword in keywords:
                            if keyword.lower() in content_lower:
                                matched_analysts.append(analyst_key)
                                break

                    # 如果匹配到了分析师，将消息添加到对应的列表
                    if matched_analysts:
                        for analyst_key in matched_analysts:
                            analyst_messages[analyst_key].append({
                                'type': msg_type,
                                'content': str(msg_content)
                            })

                except Exception as e:
                    logger.warning(f"⚠️ 处理消息时出错: {e}")
                    continue

            # 为每个有消息的分析师创建prompt
            for analyst_key, msg_list in analyst_messages.items():
                if not msg_list:
                    continue

                # 合并所有消息
                prompt_content = f"=== {analyst_mapping.get(analyst_key, analyst_key)} ===\n\n"
                for msg in msg_list:
                    prompt_content += f"\n[{msg['type'].upper()}]\n{msg['content'][:3000]}\n"

                if len(prompt_content) > 100:  # 确保内容足够长
                    prompts.append({
                        "analyst": analyst_key,
                        "analyst_name": analyst_mapping.get(analyst_key, analyst_key).replace("_", " ").title(),
                        "type": "extracted",
                        "content": prompt_content[:5000],
                        "timestamp": ""
                    })
                    logger.info(f"✅ 提取到 {analyst_key} 的prompt，共 {len(msg_list)} 条消息")

            if prompts:
                prompts_by_step = organize_prompts_by_step(prompts)
                logger.info(f"✅ 从messages中提取到 {len(prompts)} 个prompt，分为 {len(prompts_by_step)} 个步骤")
                return {
                    "success": True,
                    "data": {
                        "task_id": doc.get("task_id") or report_id,
                        "prompts": prompts,
                        "prompts_by_step": prompts_by_step,
                        "count": len(prompts),
                        "source": "messages"
                    },
                    "message": f"成功从messages中提取 {len(prompts)} 个prompt"
                }

        # 如果没有prompts字段，也没有messages字段，尝试从reports中提取
        reports = doc.get("reports", {})
        prompts = []

        report_analyst_names = {
            'bull_researcher': 'Bull Researcher',
            'bear_researcher': 'Bear Researcher',
            'risky_analyst': 'Risky Analyst',
            'safe_analyst': 'Safe Analyst',
            'neutral_analyst': 'Neutral Analyst',
            'market_report': 'Market Analyst',
            'fundamentals_report': 'Fundamentals Analyst',
            'news_report': 'News Analyst',
            'sentiment_report': 'Sentiment Analyst',
            'capital_flow_report': 'Capital Flow Analyst',
        }

        for key, value in reports.items():
            if key in report_analyst_names and isinstance(value, str) and len(value) > 100:
                prompts.append({
                    "analyst": key,
                    "analyst_name": report_analyst_names.get(key, key),
                    "type": "report_content",
                    "content": f"[注：该任务未保存原始prompt，以下为分析师生成的报告内容]\n\n{value[:4000]}",
                    "timestamp": ""
                })

        if prompts:
            prompts_by_step = organize_prompts_by_step(prompts)
            return {
                "success": True,
                "data": {
                    "task_id": doc.get("task_id") or report_id,
                    "prompts": prompts,
                    "prompts_by_step": prompts_by_step,
                    "count": len(prompts),
                    "warning": "原始prompt未保存，已提取报告内容作为参考"
                },
                "message": "已提取报告内容作为参考"
            }

        return {
            "success": True,
            "data": {
                "task_id": doc.get("task_id") or report_id,
                "prompts": [],
                "prompts_by_step": {},
                "count": 0,
                "warning": "该分析任务的prompt数据未保存到数据库"
            },
            "message": "Prompt获取成功，但该任务未保存prompt数据"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[X] 获取prompt失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("markdown", description="下载格式: markdown, json, pdf, docx"),
    user: dict = Depends(get_current_user)
):
    """下载报告

    支持的格式:
    - markdown: Markdown 格式（默认）
    - json: JSON 格式（包含完整数据）
    - docx: Word 文档格式（需要 pandoc）
    - pdf: PDF 格式（需要 pandoc 和 PDF 引擎）
    """
    try:
        logger.info(f"📥 下载报告: {report_id}, 格式: {format}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="报告不存在")

        stock_symbol = doc.get("stock_symbol", "unknown")
        analysis_date = doc.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))

        if format == "json":
            # JSON格式下载
            content = json.dumps(doc, ensure_ascii=False, indent=2, default=str)
            filename = f"{stock_symbol}_{analysis_date}_report.json"
            media_type = "application/json"

            # 返回文件流
            def generate():
                yield content.encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        elif format == "markdown":
            # Markdown格式下载
            reports = doc.get("reports", {})
            content_parts = []

            # 添加标题
            content_parts.append(f"# {stock_symbol} 分析报告")
            content_parts.append(f"**分析日期**: {analysis_date}")
            content_parts.append(f"**分析师**: {', '.join(doc.get('analysts', []))}")
            content_parts.append(f"**研究深度**: {doc.get('research_depth', 1)}")
            content_parts.append("")

            # 添加摘要
            if doc.get("summary"):
                content_parts.append("## 执行摘要")
                content_parts.append(doc["summary"])
                content_parts.append("")

            # 添加各模块内容
            for module_name, module_content in reports.items():
                if isinstance(module_content, str) and module_content.strip():
                    content_parts.append(f"## {module_name}")
                    content_parts.append(module_content)
                    content_parts.append("")

            content = "\n".join(content_parts)
            filename = f"{stock_symbol}_{analysis_date}_report.md"
            media_type = "text/markdown"

            # 返回文件流
            def generate():
                yield content.encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        elif format == "docx":
            # Word 文档格式下载
            from app.utils.report_exporter import report_exporter

            if not report_exporter.pandoc_available:
                raise HTTPException(
                    status_code=400,
                    detail="Word 导出功能不可用。请安装 pandoc: pip install pypandoc"
                )

            try:
                # 生成 Word 文档
                docx_content = report_exporter.generate_docx_report(doc)
                filename = f"{stock_symbol}_{analysis_date}_report.docx"

                # 返回文件流
                def generate():
                    yield docx_content

                return StreamingResponse(
                    generate(),
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            except Exception as e:
                logger.error(f"[X] Word 文档生成失败: {e}")
                raise HTTPException(status_code=500, detail=f"Word 文档生成失败: {str(e)}")

        elif format == "pdf":
            # PDF 格式下载
            from app.utils.report_exporter import report_exporter

            if not report_exporter.pandoc_available:
                raise HTTPException(
                    status_code=400,
                    detail="PDF 导出功能不可用。请安装 pandoc 和 PDF 引擎（wkhtmltopdf 或 LaTeX）"
                )

            try:
                # 生成 PDF 文档
                pdf_content = report_exporter.generate_pdf_report(doc)
                filename = f"{stock_symbol}_{analysis_date}_report.pdf"

                # 返回文件流
                def generate():
                    yield pdf_content

                return StreamingResponse(
                    generate(),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            except Exception as e:
                logger.error(f"[X] PDF 文档生成失败: {e}")
                raise HTTPException(status_code=500, detail=f"PDF 文档生成失败: {str(e)}")

        else:
            raise HTTPException(status_code=400, detail=f"不支持的下载格式: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[X] 下载报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
