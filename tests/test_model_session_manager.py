"""
测试模型会话管理器（简化版，不依赖 pytest）
"""
import asyncio
from pathlib import Path

from comac_purchase.model_session.model_session_manager import (
    LLMSessionManager,
    LiveSession,
    HistorySession,
    LLMSession,
    Chunk,
    SessionStatus,
    get_manager
)
from comac_purchase.config import settings


_history_folder = Path(settings.data_folder) / "model_session_history"


async def test_live_session_creation():
    """测试创建 LiveSession"""
    print("\n" + "=" * 50)
    print("测试 1: 创建 LiveSession")
    print("=" * 50)
    session = LiveSession()
    assert session.session_id is not None
    assert session.status == SessionStatus.IDLE
    print(f"✓ LiveSession 创建成功，session_id: {session.session_id}")


async def test_live_session_run_and_get_response():
    """测试 LiveSession 运行和获取响应"""
    print("\n" + "=" * 50)
    print("测试 2: LiveSession 运行和获取响应")
    print("=" * 50)
    manager = get_manager()
    
    # 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：1+1等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动（轮询直到状态变为RUNNING且_stream存在）
    session = None
    for _ in range(60):  # 最多等待60秒
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and session.status == SessionStatus.RUNNING and hasattr(session, '_stream') and session._stream:
            print(f"✓ 会话运行成功，session_id: {session_id}")
            break
    
    assert session is not None
    assert isinstance(session, LiveSession)
    assert session.session_id == session_id
    assert session.status == SessionStatus.RUNNING
    assert session_id in manager._live_sessions
    print(f"✓ 会话运行成功，session_id: {session_id}")
    
    # 获取响应
    print("\n响应内容:")
    chunks = []
    async for chunk in session.get_response():
        chunks.append(chunk)
        if chunk.delta_content:
            print(chunk.delta_content, end='', flush=True)
    print()
    
    assert len(chunks) > 0
    print(f"\n✓ 获取到 {len(chunks)} 个 chunk")
    
    # 等待会话完成
    if session._run_task:
        await session._run_task
    
    # 等待会话状态变为 FINISHED
    for _ in range(30):
        await asyncio.sleep(0.1)
        status = manager.get_session_status(session_id)
        if status == SessionStatus.FINISHED:
            break
    
    # 验证会话状态为 FINISHED
    final_status = manager.get_session_status(session_id)
    assert final_status == SessionStatus.FINISHED
    print(f"✓ 会话完成，状态: {final_status.value}")


async def test_manager_get_session_from_live():
    """测试从管理器获取活跃会话"""
    print("\n" + "=" * 50)
    print("测试 3: 从管理器获取活跃会话")
    print("=" * 50)
    manager = get_manager()
    
    # 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：2+2等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动
    session = None
    for _ in range(10):
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and session.status == SessionStatus.RUNNING:
            break
    
    # 从管理器获取会话（应该是活跃会话）
    retrieved_session = manager.get_session(session_id)
    assert retrieved_session is not None
    assert isinstance(retrieved_session, LiveSession)
    assert retrieved_session.session_id == session_id
    print(f"✓ 从管理器获取到活跃会话: {session_id}")
    
    # 等待会话完成
    if session._run_task:
        await session._run_task


async def test_manager_get_session_from_history():
    """测试从管理器获取历史会话"""
    print("\n" + "=" * 50)
    print("测试 4: 从管理器获取历史会话")
    print("=" * 50)
    manager = get_manager()
    
    # 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：3+3等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动
    session = None
    for _ in range(10):
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and session.status == SessionStatus.RUNNING:
            break
    
    # 等待会话完成
    if session and hasattr(session, '_run_task') and session._run_task:
        await session._run_task
    
    # 等待会话状态变为 FINISHED
    for _ in range(60):
        await asyncio.sleep(1)
        try:
            status = manager.get_session_status(session_id)
            if status == SessionStatus.FINISHED:
                break
        except:
            pass
    
    # 验证会话状态为 FINISHED
    final_status = manager.get_session_status(session_id)
    assert final_status == SessionStatus.FINISHED, f"会话状态为 {final_status.value}"
    assert session_id not in manager._live_sessions, f"会话ID {session_id} 在活跃列表中"
    print(f"✓ 会话已从活跃列表中移除，状态: {final_status.value}")
    
    # 从管理器获取会话（应该是历史会话）
    retrieved_session = manager.get_session(session_id)
    assert retrieved_session is not None
    assert isinstance(retrieved_session, HistorySession)
    assert retrieved_session.session_id == session_id
    print(f"✓ 从管理器获取到历史会话: {session_id}")


async def test_history_session_get_response():
    """测试历史会话获取响应"""
    print("\n" + "=" * 50)
    print("测试 5: 历史会话获取响应")
    print("=" * 50)
    manager = get_manager()
    
    # 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：4+4等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动
    session = None
    for _ in range(20):
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and session.status == SessionStatus.RUNNING:
            break
    
    # 等待会话完成
    if session and hasattr(session, '_run_task') and session._run_task:
        await session._run_task
    
    # 等待会话状态变为 FINISHED
    for _ in range(60):
        await asyncio.sleep(1)
        try:
            status = manager.get_session_status(session_id)
            if status == SessionStatus.FINISHED:
                break
        except:
            pass
    
    # 验证会话状态为 FINISHED
    final_status = manager.get_session_status(session_id)
    assert final_status == SessionStatus.FINISHED
    
    # 从管理器获取历史会话
    history_session = manager.get_session(session_id)
    assert history_session is not None
    assert isinstance(history_session, HistorySession)
    assert history_session.status == SessionStatus.FINISHED
    
    # 获取响应
    print("\n历史会话响应:")
    chunks = []
    async for chunk in history_session.get_response():
        chunks.append(chunk)
        if chunk.delta_content:
            print(f"[历史会话响应] {chunk.delta_content[:100]}...")
    
    assert len(chunks) == 1  # 历史会话应该只返回一个完整的chunk
    assert chunks[0].delta_content is not None
    print(f"✓ 历史会话响应获取成功，内容长度: {len(chunks[0].delta_content or '')}")


async def test_get_response_first_chunk_is_history():
    """测试 get_response 的第一个 Chunk 是历史所有 chunk 拼接而成"""
    print("\n" + "=" * 50)
    print("测试 6: get_response 的第一个 Chunk 是历史 chunk 拼接")
    print("=" * 50)
    manager = get_manager()
    
    # 创建会话并设置历史chunk
    session = LiveSession()
    history_chunks = [
        Chunk(delta_content="历史内容1"),
        Chunk(delta_content="历史内容2"),
        Chunk(delta_reasoning_content="历史推理1")
    ]
    session.set_history_chunks(history_chunks)
    
    # 运行会话
    messages = [{"role": "user", "content": "请用一句话回答：5+5等于几？"}]
    manager._register_live_session(session)
    await session.run(messages)
    
    # 获取响应
    print("\n响应内容（包含历史chunk）:")
    chunks = []
    async for chunk in session.get_response():
        chunks.append(chunk)
        if chunk.delta_content:
            print(chunk.delta_content, end='', flush=True)
    print()
    
    # 验证第一个chunk是历史chunk拼接
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert first_chunk.delta_content == "历史内容1历史内容2"
    assert first_chunk.delta_reasoning_content == "历史推理1"
    assert first_chunk.stream == False
    print(f"\n✓ 第一个chunk是历史chunk拼接: {first_chunk.delta_content}")
    
    # 等待会话完成
    if session._run_task:
        await session._run_task


async def test_session_stop():
    """测试停止会话"""
    print("\n" + "=" * 50)
    print("测试 7: 停止会话")
    print("=" * 50)
    manager = get_manager()
    
    # 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：6+6等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动
    session = None
    for _ in range(10):
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and session.status == SessionStatus.RUNNING:
            break
    
    # 等待一小段时间让会话开始
    await asyncio.sleep(0.5)
    
    # 停止会话
    await session.stop()
    
    # 验证会话已停止
    assert session.status == SessionStatus.STOPPED
    assert session_id not in manager._live_sessions
    print(f"✓ 会话已停止: {session_id}")
    
    # 验证可以从管理器获取历史会话
    retrieved_session = manager.get_session(session_id)
    assert isinstance(retrieved_session, HistorySession)
    assert retrieved_session.status == SessionStatus.STOPPED
    print(f"✓ 停止的会话已保存为历史会话")


async def test_session_persistence():
    """测试会话持久化"""
    print("\n" + "=" * 50)
    print("测试 8: 会话持久化")
    print("=" * 50)
    manager = get_manager()
    
    # 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：7+7等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动并完成
    session = None
    for _ in range(10):
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and session.status == SessionStatus.RUNNING or session.status == SessionStatus.FINISHED:
            break
    
    # 等待会话完成
    if session and hasattr(session, '_run_task') and session._run_task:
        await session._run_task
    
    # 等待会话状态变为 FINISHED
    for _ in range(60):
        await asyncio.sleep(1)
        try:
            status = manager.get_session_status(session_id)
            if status == SessionStatus.FINISHED:
                break
        except:
            pass
    
    # 验证会话状态为 FINISHED
    final_status = manager.get_session_status(session_id)
    assert final_status == SessionStatus.FINISHED
    
    # 验证文件已保存
    file_path = _history_folder / f"{session_id}.json"
    assert file_path.exists()
    print(f"✓ 会话文件已保存: {file_path}")
    
    # 验证可以从文件加载
    history_session = HistorySession.from_file(session_id)
    assert history_session is not None
    assert history_session.session_id == session_id
    assert history_session.content is not None
    print(f"✓ 会话可以从文件加载: {session_id}")


async def test_integration():
    """集成测试：完整流程"""
    print("\n" + "=" * 50)
    print("测试 9: 集成测试 - 完整流程")
    print("=" * 50)
    
    manager = get_manager()
    
    # 1. 创建并运行会话
    messages = [{"role": "user", "content": "请用一句话回答：8+8等于几？"}]
    session_id = await manager.create_and_run_session(messages)
    
    # 等待会话启动（确保_stream存在）
    session = None
    for _ in range(30):
        await asyncio.sleep(0.1)
        session = manager.get_session(session_id)
        if session and isinstance(session, LiveSession) and session.status in [SessionStatus.RUNNING, SessionStatus.FINISHED]:
            if hasattr(session, '_stream') and session._stream:
                break
    
    assert session is not None
    assert isinstance(session, LiveSession)
    print(f"\n1. 创建会话: {session_id}")
    
    # 2. 获取响应
    print("\n2. 获取响应:")
    async for chunk in session.get_response():
        if chunk.delta_content:
            print(chunk.delta_content, end='', flush=True)
    print()
    
    # 3. 等待完成
    if hasattr(session, '_run_task') and session._run_task:
        await session._run_task
    
    # 等待会话状态变为 FINISHED
    for _ in range(60):
        await asyncio.sleep(1)
        try:
            status = manager.get_session_status(session_id)
            if status == SessionStatus.FINISHED:
                break
        except:
            pass
    
    # 验证会话状态为 FINISHED
    final_status = manager.get_session_status(session_id)
    assert final_status == SessionStatus.FINISHED
    print(f"\n3. 会话完成，状态: {final_status.value}")
    
    # 4. 验证已从活跃列表移除
    assert session_id not in manager._live_sessions
    print(f"4. 会话已从活跃列表移除")
    
    # 5. 从管理器获取历史会话
    retrieved_session = manager.get_session(session_id)
    assert isinstance(retrieved_session, HistorySession)
    print(f"5. 从管理器获取历史会话成功")
    
    # 6. 从历史会话获取响应
    print("\n6. 从历史会话获取响应:")
    async for chunk in retrieved_session.get_response():
        if chunk.delta_content:
            print(f"[历史] {chunk.delta_content[:100]}...")
    
    print("\n" + "=" * 50)
    print("集成测试完成 ✓")
    print("=" * 50)


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("开始运行所有测试")
    print("=" * 70)
    
    tests = [
        test_live_session_creation,
        test_live_session_run_and_get_response,
        test_manager_get_session_from_live,
        test_manager_get_session_from_history,
        test_history_session_get_response,
        test_get_response_first_chunk_is_history,
        test_session_stop,
        test_session_persistence,
        test_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ 测试失败: {test_func.__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"测试完成: 通过 {passed} 个，失败 {failed} 个")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

