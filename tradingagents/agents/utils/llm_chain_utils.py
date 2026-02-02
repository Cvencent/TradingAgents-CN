"""
LLM链创建工具模块

提供统一的LLM链创建和工具绑定封装，支持多种模型格式（包括DeepSeek/302AI等）
"""

from typing import List, Callable, Any, Optional, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger

logger = get_logger("agents.llm_chain_utils")


def is_deepseek_model(llm: BaseLanguageModel) -> bool:
    """
    检查是否为DeepSeek模型（包括302AI的DeepSeek格式）
    
    Args:
        llm: LLM模型实例
        
    Returns:
        bool: 是否为DeepSeek模型
    """
    if not hasattr(llm, '__class__'):
        return False
    
    class_name = llm.__class__.__name__
    model_name = getattr(llm, 'model_name', '') or getattr(llm, 'model', '')
    
    # 检查类名或模型名是否包含DeepSeek相关标识
    deepseek_indicators = ['DeepSeek', 'deepseek', 'DEEPSEEK']
    is_deepseek = any(indicator in class_name for indicator in deepseek_indicators)
    is_deepseek_model_name = any(indicator in model_name for indicator in deepseek_indicators)
    
    # 检查是否为302AI的DeepSeek模型
    is_302ai_deepseek = '302' in str(model_name) and 'deepseek' in str(model_name).lower()
    
    return is_deepseek or is_deepseek_model_name or is_302ai_deepseek


def is_302ai_model(llm: BaseLanguageModel) -> bool:
    """
    检查是否为302AI模型
    
    Args:
        llm: LLM模型实例
        
    Returns:
        bool: 是否为302AI模型
    """
    if not hasattr(llm, '__class__'):
        return False
    
    model_name = getattr(llm, 'model_name', '') or getattr(llm, 'model', '')
    base_url = getattr(llm, 'openai_api_base', '') or getattr(llm, 'base_url', '')
    
    # 检查模型名或base_url是否包含302AI相关标识
    indicators = ['302', '302ai', '302.ai']
    is_302ai_model = any(indicator in str(model_name).lower() for indicator in indicators)
    is_302ai_url = any(indicator in str(base_url).lower() for indicator in indicators)
    
    return is_302ai_model or is_302ai_url


def get_model_info(llm: BaseLanguageModel) -> dict:
    """
    获取模型信息
    
    Args:
        llm: LLM模型实例
        
    Returns:
        dict: 包含模型类型信息的字典
    """
    info = {
        'class_name': llm.__class__.__name__,
        'model_name': getattr(llm, 'model_name', '') or getattr(llm, 'model', 'unknown'),
        'is_deepseek': is_deepseek_model(llm),
        'is_302ai': is_302ai_model(llm),
        'is_google': 'Google' in llm.__class__.__name__ or 'Gemini' in llm.__class__.__name__,
        'is_openai': 'OpenAI' in llm.__class__.__name__ and 'Azure' not in llm.__class__.__name__,
    }
    
    # 确定模型类别
    # 🔥 注意：302AI 独立分类，因为它支持标准工具调用，与原生DeepSeek不同
    if info['is_302ai']:
        info['model_category'] = '302ai'
    elif info['is_deepseek']:
        info['model_category'] = 'deepseek'
    elif info['is_google']:
        info['model_category'] = 'google'
    elif info['is_openai']:
        info['model_category'] = 'openai'
    else:
        info['model_category'] = 'other'
    
    return info


def create_llm_chain(
    prompt: ChatPromptTemplate,
    llm: BaseLanguageModel,
    tools: Optional[List[Callable]] = None,
    bind_tools: bool = True,
    analyst_name: str = "未知分析师"
) -> Any:
    """
    创建LLM链，自动处理不同模型的工具绑定
    
    支持以下模型类型：
    - DeepSeek模型（包括302AI的DeepSeek格式）：不使用bind_tools，通过prompt引导工具调用
    - Google模型：使用标准bind_tools，但需要特殊处理工具调用结果
    - OpenAI/其他模型：使用标准bind_tools
    
    Args:
        prompt: ChatPromptTemplate提示模板
        llm: LLM模型实例
        tools: 工具列表（可选）
        bind_tools: 是否绑定工具（默认True）
        analyst_name: 分析师名称（用于日志）
        
    Returns:
        配置好的chain对象
        
    Example:
        >>> chain = create_llm_chain(
        ...     prompt=prompt_template,
        ...     llm=llm_instance,
        ...     tools=[tool1, tool2],
        ...     analyst_name="基本面分析师"
        ... )
        >>> result = chain.invoke({"messages": messages})
    """
    model_info = get_model_info(llm)
    
    logger.info(f"[{analyst_name}] 创建LLM链")
    logger.info(f"[{analyst_name}] 模型类别: {model_info['model_category']}")
    logger.info(f"[{analyst_name}] 模型名称: {model_info['model_name']}")
    
    # 根据模型类型创建链
    if model_info['model_category'] == '302ai':
        # 🔥 302AI 平台：使用标准 bind_tools，DeepSeek适配器会特殊处理
        # DeepSeek适配器会检测302AI并使用正确的参数格式（tool-use-mode=1）
        logger.info(f"[{analyst_name}] 302AI平台模型，使用标准工具绑定（适配器自动处理302AI特殊参数）")
        
        if tools and bind_tools:
            try:
                # 302AI通过DeepSeek适配器处理，支持标准bind_tools
                chain = prompt | llm.bind_tools(tools)
                logger.info(f"[{analyst_name}] ✅ 302AI链创建成功（绑定{len(tools)}个工具）")
            except Exception as e:
                logger.warning(f"[{analyst_name}] 302AI工具绑定失败: {e}，降级为提示词模式")
                chain = prompt | llm
        else:
            chain = prompt | llm
            logger.info(f"[{analyst_name}] ✅ 302AI链创建成功（无工具）")
    elif model_info['model_category'] == 'deepseek':
        # 原生DeepSeek模型（非302AI）：不使用bind_tools，直接使用原有prompt
        logger.info(f"[{analyst_name}] 原生DeepSeek模型，使用简化工具调用方式（不绑定工具）")
        
        # 对于原生DeepSeek模型，不使用bind_tools，直接返回prompt | llm
        # 工具信息已经在prompt中通过tool_names变量传递
        chain = prompt | llm
        
        if tools and bind_tools:
            logger.info(f"[{analyst_name}] ✅ DeepSeek链创建成功（{len(tools)}个工具通过prompt传递）")
        else:
            logger.info(f"[{analyst_name}] ✅ DeepSeek链创建成功（无工具）")
            
    elif model_info['model_category'] == 'google':
        # Google模型：使用标准bind_tools
        logger.info(f"[{analyst_name}] Google模型，使用标准工具绑定")
        
        if tools and bind_tools:
            chain = prompt | llm.bind_tools(tools)
            logger.info(f"[{analyst_name}] ✅ Google链创建成功（绑定{len(tools)}个工具）")
        else:
            chain = prompt | llm
            logger.info(f"[{analyst_name}] ✅ Google链创建成功（无工具）")
            
    else:
        # OpenAI/其他模型：使用标准bind_tools
        logger.info(f"[{analyst_name}] {model_info['model_category']}模型，使用标准工具绑定")
        
        if tools and bind_tools:
            try:
                chain = prompt | llm.bind_tools(tools)
                logger.info(f"[{analyst_name}] ✅ 链创建成功（绑定{len(tools)}个工具）")
            except Exception as e:
                logger.warning(f"[{analyst_name}] 工具绑定失败: {e}，创建无工具链")
                chain = prompt | llm
        else:
            chain = prompt | llm
            logger.info(f"[{analyst_name}] ✅ 链创建成功（无工具）")
    
    return chain


def should_use_tool_call_handler(llm: BaseLanguageModel) -> bool:
    """
    判断是否需要使用Google工具调用处理器
    
    注意：302AI模型使用标准工具调用流程，不需要Google特殊处理
    
    Args:
        llm: LLM模型实例
        
    Returns:
        bool: 是否需要使用GoogleToolCallHandler
    """
    model_info = get_model_info(llm)
    # 只有Google模型需要特殊处理，302AI使用标准流程
    return model_info['model_category'] == 'google' and not model_info['is_302ai']


def log_model_usage(llm: BaseLanguageModel, analyst_name: str = "未知分析师"):
    """
    记录模型使用信息（用于调试）
    
    Args:
        llm: LLM模型实例
        analyst_name: 分析师名称
    """
    model_info = get_model_info(llm)
    
    logger.info(f"=" * 60)
    logger.info(f"[{analyst_name}] 模型使用信息")
    logger.info(f"=" * 60)
    logger.info(f"  类名: {model_info['class_name']}")
    logger.info(f"  模型名: {model_info['model_name']}")
    logger.info(f"  模型类别: {model_info['model_category']}")
    logger.info(f"  是否DeepSeek: {model_info['is_deepseek']}")
    logger.info(f"  是否302AI: {model_info['is_302ai']}")
    logger.info(f"  是否Google: {model_info['is_google']}")
    logger.info(f"=" * 60)
