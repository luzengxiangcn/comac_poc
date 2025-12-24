"""
模型会话管理器
用于管理所有的 LLMSession 实例
"""
import asyncio
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Any
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel
from openai import AsyncOpenAI

from comac_purchase.config import settings
from comac_purchase.model_session.model import openai_client


_history_folder = Path(settings.data_folder) / "model_session_history"


class Chunk(BaseModel):
    """响应块"""
    stream: bool = True
    delta_content: Optional[str] = None
    delta_reasoning_content: Optional[str] = None
    
    def is_reasoning_content(self) -> bool:
        """判断是否为推理内容"""
        return self.delta_reasoning_content is not None


class SessionStatus(Enum):
    """会话状态"""
    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    STOPPED = "stopped"  # 已停止
    FINISHED = "finished"  # 已完成
    ERROR = "error"  # 错误


class HistorySessionData(BaseModel):
    """历史会话数据（用于序列化）"""
    session_id: str
    status: SessionStatus
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    description: Optional[Dict[str, Any]] = None


class NotExistError(Exception):
    """会话不存在异常"""
    pass




class LLMSession(ABC):
    """LLM会话基类"""
    
    def __init__(self, session_id: str, status: SessionStatus):
        """
        初始化会话
        
        Args:
            session_id: 会话 ID
            status: 会话状态
        """
        self.session_id = session_id
        self._status = status
    
    @property
    def status(self) -> SessionStatus:
        """获取当前状态"""
        return self._status
    
    @abstractmethod
    async def get_response(self) -> AsyncGenerator[Chunk, None]:
        """
        获取响应（生成器）
        第一个 Chunk 是历史所有 chunk 拼接而成
        
        Yields:
            Chunk: 响应块对象
        """
        pass


class LiveSession(LLMSession):
    """执行中的会话"""
    
    def __init__(
        self, 
        client: Optional[AsyncOpenAI] = None, 
        description: Optional[dict] = None, 
        session_id: Optional[str] = None
    ):
        """
        初始化执行中的会话
        
        Args:
            client: OpenAI 客户端实例，如果不提供则使用默认客户端
            description: 会话描述信息
            session_id: 会话 ID，如果不提供则自动生成
        """
        session_id = session_id or self._generate_session_id()
        super().__init__(session_id, SessionStatus.IDLE)
        self.client = client or openai_client
        self._messages: List[Dict[str, str]] = []
        self._stream: Optional[Any] = None
        self.response_list: List[Chunk] = []  # 响应列表，run中不断append，记录完整内容
        self._run_task: Optional[asyncio.Task] = None  # run的后台任务
        self._stop_event = False
        self._condition = asyncio.Condition()  # 用于通知新内容到达
        self._description = description or {}
        self._history_chunks: List[Chunk] = []  # 历史chunk列表（用于get_response的第一个chunk）
        self._manager = None  # 延迟设置，避免循环引用
    
    @staticmethod
    def _generate_session_id() -> str:
        """
        生成新的会话 ID
        
        Returns:
            会话 ID（UUID）
        """
        return str(uuid4())
    
    def _parse_chunk(self, chunk: Any) -> Chunk:
        """
        解析原始 chunk 为 Chunk 类
        
        Args:
            chunk: 原始 chunk 对象
            
        Returns:
            Chunk 对象
        """
        delta_content = None
        delta_reasoning_content = None
        
        if hasattr(chunk, 'choices') and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                delta_content = delta.content
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                delta_reasoning_content = delta.reasoning_content
        
        return Chunk(
            delta_content=delta_content,
            delta_reasoning_content=delta_reasoning_content
        )
    
    def _extract_content(self) -> str:
        """
        从 response_list 中提取 content
        
        Returns:
            合并后的文本内容
        """
        content_parts = []
        for chunk in self.response_list:
            if isinstance(chunk, Chunk) and chunk.delta_content:
                content_parts.append(chunk.delta_content)
        return ''.join(content_parts)
    
    def _extract_reasoning_content(self) -> str:
        """
        从 response_list 中提取 reasoning_content
        
        Returns:
            合并后的推理内容
        """
        reasoning_parts = []
        for chunk in self.response_list:
            if isinstance(chunk, Chunk) and chunk.delta_reasoning_content:
                reasoning_parts.append(chunk.delta_reasoning_content)
        return ''.join(reasoning_parts)
    
    def _save_to_file(self, status: SessionStatus) -> None:
        """
        保存会话数据到文件
        确保数据真正写入磁盘后再返回
        
        Args:
            status: 要保存的状态
        """
        _history_folder.mkdir(parents=True, exist_ok=True)
        file_path = _history_folder / f"{self.session_id}.json"
        
        history_data = HistorySessionData(
            session_id=self.session_id,
            status=status,
            content=self._extract_content(),
            reasoning_content=self._extract_reasoning_content(),
            messages=self._messages,
            description=self._description
        )
        
        # 使用 with 语句保存数据，确保文件正确关闭
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history_data.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
            # 强制刷新缓冲区并同步到磁盘
            f.flush()
            os.fsync(f.fileno())
    
    async def _save_and_convert_to_history(self, status: SessionStatus) -> 'HistorySession':
        """
        保存会话信息到文件并转换为 HistorySession
        
        Args:
            status: 要保存的状态
            
        Returns:
            HistorySession 实例
        """
        try:
            # 先保存数据，确保数据已保存并落盘
            self._save_to_file(status=status)
            # 数据保存成功后再更新内存状态
            self._status = status
            
            # 转换为 HistorySession
            history_session = HistorySession(
                session_id=self.session_id,
                status=status,
                content=self._extract_content(),
                reasoning_content=self._extract_reasoning_content(),
                messages=self._messages,
                description=self._description
            )
            
            return history_session
        
        except Exception as e:
            print(f"保存会话数据失败: {str(e)}")
            raise RuntimeError(f"保存会话数据失败: {str(e)}")
    
    async def _consume_stream(self) -> None:
        """
        后台任务：消费流并将完整chunk append到response_list
        每次append后通知等待的生成器
        """
        try:
            async for chunk in self._stream:
                # 检查是否被停止
                if self._stop_event:
                    break
                
                # 解析 chunk 为 Chunk 类
                parsed_chunk = self._parse_chunk(chunk)
                
                # 将解析后的 chunk append到response_list
                async with self._condition:
                    self.response_list.append(parsed_chunk)
                    # 通知所有等待的生成器有新内容
                    self._condition.notify_all()
                
                # 检查是否完成
                if hasattr(chunk, 'choices') and chunk.choices:
                    finish_reason = chunk.choices[0].finish_reason
                    if finish_reason:
                        break
            
            # 流消费完成，更新状态并通知
            async with self._condition:
                if self._status == SessionStatus.RUNNING:
                    # 转换为 HistorySession 并保存
                    history_session = await self._save_and_convert_to_history(SessionStatus.FINISHED)
                    # 从管理器中删除并注册历史会话
                    if self._manager:
                        self._manager._unregister_live_session(self.session_id)
                        self._manager._register_history_session(history_session)
                # 最后通知一次，确保所有等待的生成器都能退出
                self._condition.notify_all()
        
        except Exception as e:
            async with self._condition:
                # 转换为 HistorySession 并保存
                try:
                    history_session = await self._save_and_convert_to_history(SessionStatus.ERROR)
                    if self._manager:
                        self._manager._unregister_live_session(self.session_id)
                        self._manager._register_history_session(history_session)
                except:
                    pass
                self._condition.notify_all()
            raise RuntimeError(f"消费流失败: {str(e)}")
    
    async def run(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-ai/DeepSeek-V3.2-Exp",
        stream: bool = True,
        **kwargs
    ) -> None:
        """
        异步运行模型会话
        启动后台任务消费流，不断append到response_list
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认为 "deepseek-ai/DeepSeek-V3.2-Exp"
            stream: 是否使用流式响应，默认为 True
            **kwargs: 其他 OpenAI API 参数
        """
        if self._status == SessionStatus.RUNNING:
            raise RuntimeError("会话已在运行中，请先停止当前会话")
        
        self._status = SessionStatus.RUNNING
        self._stop_event = False
        self._messages = messages
        self.response_list = []  # 重置响应列表
        
        try:
            # 创建流式请求（带重试机制，已在客户端中实现）
            self._stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
            
            # 启动后台任务消费流
            self._run_task = asyncio.create_task(self._consume_stream())
        
        except Exception as e:
            # 如果启动失败，也要保存并转换
            try:
                await self._save_and_convert_to_history(SessionStatus.ERROR)
                if self._manager:
                    self._manager._unregister_live_session(self.session_id)
            except:
                pass
            raise RuntimeError(f"启动会话失败: {str(e)}")
    
    async def stop(self) -> None:
        """
        异步停止会话
        """
        if self._status == SessionStatus.RUNNING:
            self._stop_event = True
            # 取消后台任务
            if self._run_task and not self._run_task.done():
                self._run_task.cancel()
                try:
                    await self._run_task
                except asyncio.CancelledError:
                    pass
            # 关闭流
            if self._stream:
                if hasattr(self._stream, 'close'):
                    await self._stream.close()
                self._stream = None
            # 转换为 HistorySession 并保存
            history_session = await self._save_and_convert_to_history(SessionStatus.STOPPED)
            if self._manager:
                self._manager._unregister_live_session(self.session_id)
                self._manager._register_history_session(history_session)
        elif self._status == SessionStatus.IDLE:
            # 如果已经是空闲状态，不需要操作
            pass
        else:
            # 转换为 HistorySession 并保存
            history_session = await self._save_and_convert_to_history(SessionStatus.STOPPED)
            if self._manager:
                self._manager._unregister_live_session(self.session_id)
                self._manager._register_history_session(history_session)
    
    def set_history_chunks(self, chunks: List[Chunk]) -> None:
        """
        设置历史chunk列表（用于get_response的第一个chunk）
        
        Args:
            chunks: 历史chunk列表
        """
        self._history_chunks = chunks
    
    async def get_response(self) -> AsyncGenerator[Chunk, None]:
        """
        异步获取响应（生成器）
        第一个 Chunk 是历史所有 chunk 拼接而成
        然后从当前位置yield到列表末尾
        支持多个客户端并发消费，每个从自己的位置开始
        
        Yields:
            Chunk: 响应内容（完整的chunk对象）
            
        Raises:
            RuntimeError: 如果会话未运行或已停止
        """
        # 首先yield历史chunk拼接后的第一个chunk
        if self._history_chunks:
            # 拼接历史chunk
            history_content = ''.join([
                chunk.delta_content or '' 
                for chunk in self._history_chunks 
                if chunk.delta_content
            ])
            history_reasoning_content = ''.join([
                chunk.delta_reasoning_content or '' 
                for chunk in self._history_chunks 
                if chunk.delta_reasoning_content
            ])
            
            if history_content or history_reasoning_content:
                yield Chunk(
                    stream=False,
                    delta_content=history_content if history_content else None,
                    delta_reasoning_content=history_reasoning_content if history_reasoning_content else None
                )
        
        if self._status == SessionStatus.IDLE:
            raise RuntimeError("会话未运行，请先调用 run() 方法")

        if self._status != SessionStatus.RUNNING:
            # 如果已经完成，尝试从 HistorySession 中获取响应
            if self._manager:
                history_session = self._manager.get_session(self.session_id)
                if isinstance(history_session, HistorySession):
                    # 从 HistorySession 获取响应
                    async for chunk in history_session.get_response():
                        yield chunk
                    return
            
            # 如果无法从 HistorySession 获取，则返回 response_list（向后兼容）
            for chunk in self.response_list:
                yield chunk
            return
        
        # 此时会话处于 RUNNING 状态，但存在一个竞态条件：
        # 前端可能在刚触发 run() 后立刻调用 get_response()，
        # 而 run() 内部先将状态置为 RUNNING，再去创建流对象 self._stream，
        # 在这极短时间窗口内，_stream 仍为 None，response_list 也为空，
        # 如果直接抛错会导致前端看到“流对象不存在，请先调用 run() 方法”。
        #
        # 为了避免这种“点得太快”的错误，这里增加一个短暂等待逻辑，
        # 给 run() 一点时间完成流的创建或至少产生首个 response_list。
        import asyncio
        max_wait_times = 20  # 最多等待约 2 秒（20 * 0.1s）
        wait_count = 0
        while (
            self._status == SessionStatus.RUNNING
            and not self._stream
            and not self.response_list
            and wait_count < max_wait_times
        ):
            await asyncio.sleep(0.1)
            wait_count += 1
        
        # 等待之后重新判断状态
        if self._status != SessionStatus.RUNNING:
            # 如果在等待过程中已经结束或出错，走上面的“非 RUNNING”逻辑
            if self._manager:
                history_session = self._manager.get_session(self.session_id)
                if isinstance(history_session, HistorySession):
                    async for chunk in history_session.get_response():
                        yield chunk
                    return
            for chunk in self.response_list:
                yield chunk
            return
        
        # 如果仍然既没有流对象也没有任何内容，说明底层还没真正开始返回，
        # 直接返回即可，相当于一个“空流”，避免抛出误导性错误。
        if not self._stream and not self.response_list:
            return
        
        # 每个生成器维护自己的位置指针（索引位置）
        current_index = 0
        
        # 循环检查，直到run结束且当前位置等于列表长度
        while True:
            async with self._condition:
                # 获取当前列表长度
                list_length = len(self.response_list)
                
                # 从当前位置（索引）到列表长度，yield所有新内容
                while current_index < list_length:
                    yield self.response_list[current_index]
                    current_index += 1
                
                # 如果run已结束（状态为FINISHED或STOPPED）且当前位置等于列表长度，退出
                if self._status in [SessionStatus.FINISHED, SessionStatus.STOPPED, SessionStatus.ERROR]:
                    if current_index >= list_length:
                        break
                
                # 如果还在运行中，等待新内容到达（事件通知，不消耗CPU）
                if self._status == SessionStatus.RUNNING:
                    # 等待条件通知，有新内容或状态改变时会唤醒
                    await self._condition.wait()
                else:
                    # 状态已改变，继续循环以处理剩余内容或检查退出条件
                    continue


class HistorySession(LLMSession):
    """执行完的会话"""
    
    def __init__(
        self,
        session_id: str,
        status: SessionStatus,
        content: Optional[str] = None,
        reasoning_content: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        description: Optional[Dict[str, Any]] = None
    ):
        """
        初始化历史会话
        
        Args:
            session_id: 会话 ID
            status: 会话状态
            content: 文本内容
            reasoning_content: 推理内容
            messages: 消息列表
            description: 会话描述
        """
        super().__init__(session_id, status)
        self.content = content
        self.reasoning_content = reasoning_content
        self.messages = messages
        self.description = description
    
    @classmethod
    def from_file(cls, session_id: str) -> Optional['HistorySession']:
        """
        从文件加载历史会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            HistorySession 实例，如果不存在返回 None
        """
        file_path = _history_folder / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = HistorySessionData.model_validate_json(f.read())
                return cls(
                    session_id=data.session_id,
                    status=data.status,
                    content=data.content,
                    reasoning_content=data.reasoning_content,
                    messages=data.messages,
                    description=data.description
                )
        except (FileNotFoundError, IOError, Exception) as e:
            print(f"读取历史会话文件失败: {str(e)}")
            return None
    
    async def get_response(self) -> AsyncGenerator[Chunk, None]:
        """
        获取响应（生成器）
        第一个 Chunk 是历史所有 chunk 拼接而成（对于历史会话，就是完整内容）
        
        Yields:
            Chunk: 响应块对象
        """
        # 对于历史会话，直接返回完整内容作为第一个chunk
        yield Chunk(
            stream=False,
            delta_content=self.content,
            delta_reasoning_content=self.reasoning_content
        )


class LLMSessionManager:
    """LLM会话管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self._live_sessions: Dict[str, LiveSession] = {}
        self._history_session_cache_set: set[str] = set()
        # 初始化时扫描历史文件
        _history_folder.mkdir(parents=True, exist_ok=True)
        for file in _history_folder.glob("*.json"):
            self._history_session_cache_set.add(file.stem)
    
    def _register_live_session(self, session: LiveSession) -> None:
        """
        注册活跃会话到管理器
        
        Args:
            session: LiveSession 实例
        """
        self._live_sessions[session.session_id] = session
        session._manager = self
    
    def _unregister_live_session(self, session_id: str) -> None:
        """
        从管理器中删除活跃会话
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self._live_sessions:
            del self._live_sessions[session_id]
            self._history_session_cache_set.add(session_id)
    
    def _register_history_session(self, session: HistorySession) -> None:
        """
        注册历史会话到缓存
        
        Args:
            session: HistorySession 实例
        """
        self._history_session_cache_set.add(session.session_id)
    
    def get_session(self, session_id: str) -> Optional[LLMSession]:
        """
        获取会话
        先从 live_session 中取，没有则通过 session_id 去找文件，然后反序列化成 history_session
        
        Args:
            session_id: 会话 ID
            
        Returns:
            LLMSession 实例，如果不存在返回 None
        """
        # 优先从活跃会话获取
        if session_id in self._live_sessions:
            return self._live_sessions[session_id]
        
        # 从历史会话获取
        if session_id in self._history_session_cache_set:
            return HistorySession.from_file(session_id)
        
        return None
    
    def get_session_status(self, session_id: str) -> SessionStatus:
        """
        获取会话状态
        
        Args:
            session_id: 会话 ID
            
        Returns:
            SessionStatus: 会话状态
            
        Raises:
            NotExistError: 如果会话不存在（既不在活跃会话中，也不在历史会话中）
        """
        # 优先从活跃会话获取
        if session_id in self._live_sessions:
            return self._live_sessions[session_id].status
        
        # 从历史会话获取
        if session_id in self._history_session_cache_set:
            history_session = HistorySession.from_file(session_id)
            if history_session:
                return history_session.status
        
        # 如果都不存在，抛出异常
        raise NotExistError(f"会话不存在: {session_id}")
    
    async def create_and_run_session(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-ai/DeepSeek-V3.2-Exp",
        description: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        异步创建并运行会话（不等待完成）
        
        Args:
            messages: 消息列表
            model: 模型名称
            description: 会话描述
            
        Returns:
            session_id: 会话 ID
        """
        session = LiveSession(description=description)
        self._register_live_session(session)
        
        # 在后台任务中运行会话，不等待完成
        async def _run_in_background():
            try:
                await session.run(messages=messages, model=model)
            except Exception as e:
                print(f"后台运行会话失败: {str(e)}")
        
        # 启动后台任务
        asyncio.create_task(_run_in_background())
        
        # 立即返回 session_id
        return session.session_id
    
    def get_all_live_sessions(self) -> Dict[str, LiveSession]:
        """
        获取所有活跃会话
        
        Returns:
            活跃会话字典
        """
        return self._live_sessions.copy()


# 全局管理器实例
_manager = LLMSessionManager()


def get_manager() -> LLMSessionManager:
    """获取全局管理器实例"""
    return _manager
