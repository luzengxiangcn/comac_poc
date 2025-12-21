"""
OpenAI SDK 包装模块
提供重试机制以处理限流和服务过载错误
"""
import asyncio
import json
from typing import Callable, Awaitable, Any, Optional
from openai import AsyncOpenAI

from comac_purchase.config import settings


def _is_retryable_error(exception: Exception) -> bool:
    """
    判断是否为可重试的错误
    
    Args:
        exception: 异常对象
        
    Returns:
        如果是可重试的错误返回 True，否则返回 False
    """
    error_str = str(exception)
    
    # 检查 rate limiting 错误
    if ("Request was rejected due to rate limiting" in error_str or 
        "TPM limit reached" in error_str or
        "rate limiting" in error_str.lower()):
        return True
    
    # 检查 service overloaded 错误
    if ("50505" in error_str or 
        "Model service overloaded" in error_str or
        "service overloaded" in error_str.lower()):
        return True
    
    # 检查异常对象的 response 属性（OpenAI SDK 通常会有这个）
    if hasattr(exception, 'response'):
        try:
            response = exception.response
            if hasattr(response, 'text'):
                response_text = response.text
                if ("rate limiting" in response_text.lower() or 
                    "TPM limit reached" in response_text or
                    "50505" in response_text or
                    "Model service overloaded" in response_text):
                    return True
            # 尝试解析 JSON 响应体
            if hasattr(response, 'json'):
                try:
                    response_json = response.json()
                    if isinstance(response_json, dict):
                        message = response_json.get("message", "")
                        code = response_json.get("code", "")
                        if ("rate limiting" in message.lower() or 
                            "TPM limit reached" in message or
                            code == 50505 or
                            str(code) == "50505" or
                            "Model service overloaded" in message):
                            return True
                except:
                    pass
        except:
            pass
    
    # 检查异常对象的 body 属性（某些 SDK 版本）
    if hasattr(exception, 'body'):
        try:
            body = exception.body
            if isinstance(body, dict):
                message = body.get("message", "")
                code = body.get("code", "")
                if ("rate limiting" in message.lower() or 
                    "TPM limit reached" in message or
                    code == 50505 or
                    str(code) == "50505" or
                    "Model service overloaded" in message):
                    return True
            elif isinstance(body, str):
                # 尝试解析 JSON 字符串
                try:
                    body_dict = json.loads(body)
                    if isinstance(body_dict, dict):
                        message = body_dict.get("message", "")
                        code = body_dict.get("code", "")
                        if ("rate limiting" in message.lower() or 
                            "TPM limit reached" in message or
                            code == 50505 or
                            str(code) == "50505" or
                            "Model service overloaded" in message):
                            return True
                except:
                    pass
        except:
            pass
    
    # 检查异常对象的 message 属性
    if hasattr(exception, 'message'):
        try:
            message = str(exception.message)
            if ("rate limiting" in message.lower() or 
                "TPM limit reached" in message or
                "50505" in message or
                "Model service overloaded" in message):
                return True
        except:
            pass
    
    return False


async def _retry_with_backoff(
    func: Callable[[], Awaitable[Any]],
    max_wait_time: float = 8.0,
    max_retries: int = 10
) -> Any:
    """
    带指数退避的重试包装函数
    
    Args:
        func: 要执行的异步函数
        max_wait_time: 最大等待时间（秒），默认 8 秒
        max_retries: 最大重试次数，默认 10 次
        
    Returns:
        函数执行结果
        
    Raises:
        如果重试后仍然失败，抛出最后一次的异常
    """
    wait_time = 1.0  # 初始等待时间 1 秒
    last_exception = None
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if _is_retryable_error(e):
                retry_count += 1
                if retry_count >= max_retries:
                    # 达到最大重试次数，抛出异常
                    raise
                # 等待后重试
                await asyncio.sleep(wait_time)
                # 指数退避，但不超过 max_wait_time
                wait_time = min(wait_time * 2, max_wait_time)
                continue
            else:
                # 不是可重试的错误，直接抛出
                raise
    
    # 如果循环结束（理论上不会到这里），抛出最后一次异常
    if last_exception:
        raise last_exception
    raise RuntimeError("重试失败：未知错误")


class RetryableAsyncOpenAI(AsyncOpenAI):
    """
    带重试机制的 AsyncOpenAI 包装类
    自动处理限流和服务过载错误
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 10,
        max_wait_time: float = 8.0,
        **kwargs
    ):
        """
        初始化包装的 AsyncOpenAI 客户端
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            max_retries: 最大重试次数，默认 10 次
            max_wait_time: 最大等待时间（秒），默认 8 秒
            **kwargs: 其他 AsyncOpenAI 参数
        """
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        self._max_retries = max_retries
        self._max_wait_time = max_wait_time
    
    @property
    def chat(self):
        """返回包装的 chat 对象"""
        return RetryableChat(self)


class RetryableChat:
    """包装的 chat 对象，提供重试机制"""
    
    def __init__(self, client: RetryableAsyncOpenAI):
        self._client = client
    
    @property
    def completions(self):
        """返回包装的 completions 对象"""
        # 直接调用父类的 chat.completions
        original_chat = super(RetryableAsyncOpenAI, self._client).chat
        return RetryableCompletions(self._client, original_chat.completions)


class RetryableCompletions:
    """包装的 completions 对象，提供重试机制"""
    
    def __init__(self, client: RetryableAsyncOpenAI, original_completions):
        self._client = client
        self._original_completions = original_completions
    
    async def create(self, *args, **kwargs):
        """
        创建 completion，带重试机制
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            completion 结果
        """
        async def _create():
            return await self._original_completions.create(*args, **kwargs)
        
        return await _retry_with_backoff(
            _create,
            max_wait_time=self._client._max_wait_time,
            max_retries=self._client._max_retries
        )


# 创建并导出全局包装客户端实例
openai_client = RetryableAsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
    max_retries=10,
    max_wait_time=8.0
)

