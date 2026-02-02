"""
DeepSeek LLM适配器，支持Token使用统计
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import CallbackManagerForLLMRun

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_llm_logging

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger, get_logger_manager
logger = get_logger('agents')
logger = setup_llm_logging()

# 导入token跟踪器
try:
    from tradingagents.config.config_manager import token_tracker
    TOKEN_TRACKING_ENABLED = True
    logger.info("✅ Token跟踪功能已启用")
except ImportError:
    TOKEN_TRACKING_ENABLED = False
    logger.warning("⚠️ Token跟踪功能未启用")


class ChatDeepSeek(ChatOpenAI):
    """
    DeepSeek聊天模型适配器，支持Token使用统计
    
    继承自ChatOpenAI，添加了Token使用量统计功能
    """
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        初始化DeepSeek适配器
        
        Args:
            model: 模型名称，默认为deepseek-chat
            api_key: API密钥，如果不提供则从环境变量DEEPSEEK_API_KEY获取
            base_url: API基础URL
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        """
        
        # 获取API密钥
        if api_key is None:
            # 导入 API Key 验证工具
            try:
                from app.utils.api_key_utils import is_valid_api_key
            except ImportError:
                def is_valid_api_key(key):
                    if not key or len(key) <= 10:
                        return False
                    if key.startswith('your_') or key.startswith('your-'):
                        return False
                    if key.endswith('_here') or key.endswith('-here'):
                        return False
                    if '...' in key:
                        return False
                    return True

            # 从环境变量读取 API Key
            env_api_key = os.getenv("DEEPSEEK_API_KEY")

            # 验证环境变量中的 API Key 是否有效（排除占位符）
            if env_api_key and is_valid_api_key(env_api_key):
                api_key = env_api_key
                logger.info("✅ [DeepSeek初始化] 使用环境变量中的有效 API Key")
            elif env_api_key:
                logger.warning("⚠️ [DeepSeek初始化] 环境变量中的 API Key 无效（可能是占位符），将被忽略")
                api_key = None
            else:
                api_key = None

            if not api_key:
                raise ValueError(
                    "DeepSeek API密钥未找到。请在 Web 界面配置 API Key "
                    "(设置 -> 大模型厂家) 或设置 DEEPSEEK_API_KEY 环境变量。"
                )
        
        # 初始化父类
        # 使用正确的参数名称，适配302AI平台
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        self.model_name = model
        
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        生成聊天响应，并记录token使用量
        """

        # 记录开始时间
        start_time = time.time()

        # 提取并移除自定义参数，避免传递给父类
        session_id = kwargs.pop('session_id', None)
        analysis_type = kwargs.pop('analysis_type', None)

        # 检测是否为302AI平台
        # ChatOpenAI 使用 openai_api_base 属性
        base_url = getattr(self, 'openai_api_base', None) or getattr(self, 'base_url', '')
        is_302ai = '302' in (base_url or '').lower() or '302ai' in (base_url or '').lower()

        try:
            # 如果是302AI且有tools参数，需要特殊处理
            if is_302ai and 'tools' in kwargs:
                result = self._generate_with_tools_302ai(messages, stop, run_manager, **kwargs)
            else:
                # 调用父类方法生成响应
                result = super()._generate(messages, stop, run_manager, **kwargs)
            
            # 提取token使用量
            input_tokens = 0
            output_tokens = 0
            
            # 尝试从响应中提取token使用量
            if hasattr(result, 'llm_output') and result.llm_output:
                token_usage = result.llm_output.get('token_usage', {})
                if token_usage:
                    input_tokens = token_usage.get('prompt_tokens', 0)
                    output_tokens = token_usage.get('completion_tokens', 0)
            
            # 如果没有获取到token使用量，进行估算
            if input_tokens == 0 and output_tokens == 0:
                input_tokens = self._estimate_input_tokens(messages)
                output_tokens = self._estimate_output_tokens(result)
                logger.debug(f"🔍 [DeepSeek] 使用估算token: 输入={input_tokens}, 输出={output_tokens}")
            else:
                logger.info(f"📊 [DeepSeek] 实际token使用: 输入={input_tokens}, 输出={output_tokens}")
            
            # 记录token使用量
            if TOKEN_TRACKING_ENABLED and (input_tokens > 0 or output_tokens > 0):
                try:
                    # 使用提取的参数或生成默认值
                    if session_id is None:
                        session_id = f"deepseek_{hash(str(messages))%10000}"
                    if analysis_type is None:
                        analysis_type = 'stock_analysis'

                    # 记录使用量
                    usage_record = token_tracker.track_usage(
                        provider="deepseek",
                        model_name=self.model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        session_id=session_id,
                        analysis_type=analysis_type
                    )

                    if usage_record:
                        if usage_record.cost == 0.0:
                            logger.warning(f"⚠️ [DeepSeek] 成本计算为0，可能配置有问题")
                        else:
                            logger.info(f"💰 [DeepSeek] 本次调用成本: ¥{usage_record.cost:.6f}")

                        # 使用统一日志管理器的Token记录方法
                        logger_manager = get_logger_manager()
                        logger_manager.log_token_usage(
                            logger, "deepseek", self.model_name,
                            input_tokens, output_tokens, usage_record.cost,
                            session_id
                        )
                    else:
                        logger.warning(f"⚠️ [DeepSeek] 未创建使用记录")

                except Exception as track_error:
                    logger.error(f"⚠️ [DeepSeek] Token统计失败: {track_error}", exc_info=True)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [DeepSeek] 调用失败: {e}", exc_info=True)
            raise

    def _generate_with_tools_302ai(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        302AI平台的工具调用处理方法
        
        302AI支持工具调用，但需要特殊格式：
        1. 使用 tool-use-mode 参数控制工具调用模式
        2. 不使用 tool_choice 参数
        3. 使用标准的OpenAI格式tools参数
        """
        import json
        import requests
        
        logger.info(f"🔧 [DeepSeek/302AI] 使用302AI特殊工具调用格式")
        
        # 提取tools参数
        tools = kwargs.pop('tools', None)
        logger.info(f"🔧 [DeepSeek/302AI] tools参数类型: {type(tools)}")
        if tools:
            logger.info(f"🔧 [DeepSeek/302AI] tools参数内容: {tools}")
            logger.info(f"🔧 [DeepSeek/302AI] tools参数长度: {len(tools) if isinstance(tools, (list, dict)) else 'N/A'}")
        
        # 构建请求体（302AI格式）
        formatted_messages = self._format_messages_for_302ai(messages)
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": self.temperature,
        }
        logger.info(f"🔧 [DeepSeek/302AI] 格式化后的messages: {formatted_messages}")
        
        # 添加max_tokens（如果设置了）
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        
        # 添加stop（如果设置了）
        if stop:
            payload["stop"] = stop
        
        # 302AI特有：使用tool-use-mode参数（模式1=自动）
        if tools:
            payload["tools"] = tools
            payload["tool-use-mode"] = 1  # 302AI自动模式
            logger.info(f"🔧 [DeepSeek/302AI] 添加tools参数和tool-use-mode=1")
            logger.info(f"🔧 [DeepSeek/302AI] tools内容: {tools}")
        
        logger.info(f"🔧 [DeepSeek/302AI] 完整payload: {payload}")
        
        # 获取api_key（ChatOpenAI使用openai_api_key，类型为SecretStr）
        # ChatOpenAI.model_fields 中只有 'openai_api_key' 字段
        api_key = None
        try:
            openai_key = getattr(self, 'openai_api_key', None)
            if openai_key and hasattr(openai_key, 'get_secret_value'):
                api_key = openai_key.get_secret_value()
        except (AttributeError, Exception):
            pass
        
        if not api_key:
            api_key = ''
        
        # 发送请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 获取base_url（兼容ChatOpenAI的不同属性名）
        base_url = getattr(self, 'openai_api_base', None) or getattr(self, 'base_url', '')
        logger.info(f"🔧 [DeepSeek/302AI] base_url: {base_url}")
        
        # 302AI 的正确端点是 /v1/chat/completions
        # 如果 base_url 不包含 /v1，需要添加
        if not base_url.endswith('/v1') and not base_url.endswith('/v1/'):
            if base_url.endswith('/'):
                chat_url = f"{base_url}v1/chat/completions"
            else:
                chat_url = f"{base_url}/v1/chat/completions"
        else:
            chat_url = f"{base_url}/chat/completions"
        
        logger.info(f"🔧 [DeepSeek/302AI] 请求URL: {chat_url}")
        
        try:
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"❌ [DeepSeek/302AI] API错误: {error_msg[:200]}")
                raise Exception(f"API错误 {response.status_code}: {error_msg[:200]}")
            
            # 解析响应
            response_data = response.json()
            result = self._parse_302ai_response(response_data)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [DeepSeek/302AI] 网络错误: {e}")
            raise

    def _format_messages_for_302ai(self, messages) -> List[Dict]:
        """将LangChain消息格式转换为302AI格式"""
        formatted = []
        
        # 处理messages可能是一个列表的情况
        if isinstance(messages, list):
            message_list = messages
        else:
            message_list = [messages]
        
        for msg in message_list:
            # 处理tuple格式的消息（可能是 (role, content) 元组）
            if isinstance(msg, tuple):
                role, content = msg
                formatted.append({"role": str(role), "content": str(content)})
                continue
            
            # 处理字典格式的消息
            if isinstance(msg, dict):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": str(msg.get("content", ""))
                })
                continue
            
            # 处理BaseMessage对象
            if hasattr(msg, 'content'):
                if isinstance(msg, SystemMessage):
                    formatted.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    formatted.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    # 检查是否有工具调用
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        formatted.append({
                            "role": "assistant",
                            "content": msg.content or "",
                            "tool_calls": [
                                {
                                    "id": tc.get("id", f"call_{i}"),
                                    "type": "function",
                                    "function": {
                                        "name": tc.get("function", {}).get("name", ""),
                                        "arguments": tc.get("function", {}).get("arguments", "")
                                    }
                                }
                                for i, tc in enumerate(msg.tool_calls)
                            ]
                        })
                    else:
                        formatted.append({"role": "assistant", "content": msg.content})
                else:
                    formatted.append({"role": "user", "content": msg.content})
            else:
                # 未知格式，转为字符串
                formatted.append({"role": "user", "content": str(msg)})
        return formatted

    def _parse_302ai_response(self, response_data: Dict) -> ChatResult:
        """解析302AI响应并转换为LangChain格式"""
        from langchain_core.outputs import ChatGeneration
        
        choice = response_data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        finish_reason = choice.get("finish_reason", "stop")
        
        # 解析工具调用（如果有）
        tool_calls = message.get("tool_calls", [])
        
        # 构建AIMessage
        ai_message = AIMessage(content=content)
        if tool_calls:
            # LangChain 期望的格式：使用 ToolCall 对象
            # 注意：LangChain 使用 'args' 而不是 'arguments'，且 args 是字典
            from langchain_core.messages import ToolCall
            ai_message.tool_calls = [
                ToolCall(
                    name=tc.get("function", {}).get("name", ""),
                    args=json.loads(tc.get("function", {}).get("arguments", "{}")),
                    id=tc.get("id", f"call_{i}"),
                    type="function"
                )
                for i, tc in enumerate(tool_calls)
            ]
        
        # 构建ChatResult
        generation = ChatGeneration(message=ai_message)
        result = ChatResult(generations=[generation])
        
        # 提取使用量
        usage = response_data.get("usage", {})
        if usage:
            result.llm_output = {
                "token_usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
            }
        
        return result
    
    def _estimate_input_tokens(self, messages: List[BaseMessage]) -> int:
        """
        估算输入token数量
        
        Args:
            messages: 输入消息列表
            
        Returns:
            估算的输入token数量
        """
        total_chars = 0
        for message in messages:
            if hasattr(message, 'content'):
                total_chars += len(str(message.content))
        
        # 粗略估算：中文约1.5字符/token，英文约4字符/token
        # 这里使用保守估算：2字符/token
        estimated_tokens = max(1, total_chars // 2)
        return estimated_tokens
    
    def _estimate_output_tokens(self, result: ChatResult) -> int:
        """
        估算输出token数量
        
        Args:
            result: 聊天结果
            
        Returns:
            估算的输出token数量
        """
        total_chars = 0
        for generation in result.generations:
            if hasattr(generation, 'message') and hasattr(generation.message, 'content'):
                total_chars += len(str(generation.message.content))
        
        # 粗略估算：2字符/token
        estimated_tokens = max(1, total_chars // 2)
        return estimated_tokens
    
    def invoke(
        self,
        input: Union[str, List[BaseMessage], Dict[str, Any]],
        config: Optional[Dict] = None,
        **kwargs: Any,
    ) -> AIMessage:
        """
        调用模型生成响应
        
        Args:
            input: 输入消息
            config: 配置参数
            **kwargs: 其他参数（包括session_id和analysis_type）
            
        Returns:
            AI消息响应
        """
        
        # 处理输入
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        elif isinstance(input, dict) and 'messages' in input:
            # 处理包含 messages 键的字典输入
            messages = input['messages']
        else:
            messages = input
        
        # 调用生成方法
        result = self._generate(messages, **kwargs)
        
        # 返回第一个生成结果的消息
        if result.generations:
            return result.generations[0].message
        else:
            return AIMessage(content="")


def create_deepseek_llm(
    model: str = "deepseek-chat",
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    **kwargs
) -> ChatDeepSeek:
    """
    创建DeepSeek LLM实例的便捷函数
    
    Args:
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大token数
        **kwargs: 其他参数
        
    Returns:
        ChatDeepSeek实例
    """
    return ChatDeepSeek(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


# 为了向后兼容，提供别名
DeepSeekLLM = ChatDeepSeek
