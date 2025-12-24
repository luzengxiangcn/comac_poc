"""
LLM 初审检查相关的 API 路由

功能：
- 输入 project_id、supplier_id
- 检查：
    1) 采购征询文件已生成（项目有 tender_document_file_id）
    2) 该供应商有投标文件（bid_document_file_id 不为空）
    3) 投标记录的 AI初审 和 AI初审_model_session 目前为空（未在处理中）
- 触发一次使用大模型的“投标文件内容完整性”检查：
    - 使用 model_session_manager 创建会话
    - 要求大模型输出：{"reason": "...", "pass": true/false}
    - 将完整 JSON 存入 BidRecord.ai_preliminary_review
    - 将 pass 字段存入 BidRecord.ai_preliminary_review_success
    - 在任务开始时写入 BidRecord.ai_preliminary_review_model_session
    - 在任务结束后（无论成功失败）清空 BidRecord.ai_preliminary_review_model_session
"""

import asyncio
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...config import settings
from ...db import Project, BidRecord, File, get_db
from ...model_session.model_session_manager import get_manager, SessionStatus

# 日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/llm-init-check", tags=["llm-init-check"])


class AiPreliminaryReviewRequest(BaseModel):
    """AI 初审触发请求"""

    project_id: int
    supplier_id: int


class AiPreliminaryReviewAllRequest(BaseModel):
    """AI 初审（项目下所有供应商）触发请求"""

    project_id: int


async def _process_single_bid_record_async(
    bid_record_id: int,
    project_id: int,
    supplier_id: int,
    tender_file_id: str,
    bid_file_id: str,
) -> dict:
    """
    异步处理单个投标记录的AI初评（用于批量任务）：
    - 创建会话并等待完成
    - 解析结果并写回数据库
    """
    from ...db import SessionLocal

    db = SessionLocal()
    try:
        # 读取文件内容
        tender_file = db.query(File).filter(File.file_id == tender_file_id).first()
        bid_file = db.query(File).filter(File.file_id == bid_file_id).first()

        if not tender_file or not bid_file:
            return {
                "bid_record_id": bid_record_id,
                "supplier_id": supplier_id,
                "status": "failed",
                "error": "文件记录不存在",
            }

        tender_md = tender_file.read_content_as_mark_down(settings.data_folder) or ""
        bid_md = bid_file.read_content_as_mark_down(settings.data_folder) or ""

        if not tender_md or not bid_md:
            return {
                "bid_record_id": bid_record_id,
                "supplier_id": supplier_id,
                "status": "failed",
                "error": "文件内容无法读取",
            }

        # 限制长度
        max_len = 50000
        tender_md_limited = (
            tender_md[:max_len] + "...\n[内容已截断]"
            if len(tender_md) > max_len
            else tender_md
        )
        bid_md_limited = (
            bid_md[:max_len] + "...\n[内容已截断]"
            if len(bid_md) > max_len
            else bid_md
        )

        # 构建 Prompt
        prompt = f"""你是一名资深的采购评审专家，现在需要从"内容完整性"的角度，
对某个供应商的投标文件进行快速"AI 初审"，只判断是否完整响应了采购征询文件中的要求，
不需要做技术优劣或商务优劣的评价。

请对比以下两部分内容：

【一、采购征询文件（节选）】
{tender_md_limited}

【二、该供应商的投标文件（节选）】
{bid_md_limited}

请你重点从以下方面判断投标文件是否"内容完整"：
- 是否逐条（或在逻辑上）覆盖了采购征询文件中的主要技术要求、商务条款和服务承诺
- 是否缺失关键章节或关键条款（例如：技术方案、报价说明、交付计划、售后服务等）
- 是否存在明显的空白、引用错误模板、与本项目无关的大段内容等情况

请综合上述情况，给出你的结论，并严格按照下面 JSON 格式输出（不要包含任何多余文字）：
{{
  "reason": "简要说明通过/不通过的理由，50~200字左右，必须是中文",
  "pass": true 或 false   // true 表示内容基本完整，可以进入后续人工评审；false 表示内容明显不完整
}}

注意：
- 一定要返回合法的 JSON 格式
- 不要在 JSON 外再添加其他解释或文字
"""

        # 创建会话
        manager = get_manager()
        description = {
            "type": "ai_preliminary_review",
            "project_id": project_id,
            "supplier_id": supplier_id,
            "bid_record_id": bid_record_id,
            "tender_file_id": tender_file_id,
            "bid_file_id": bid_file_id,
        }

        messages = [
            {
                "role": "system",
                "content": "你是一名严谨的采购评审专家，主要负责根据采购征询文件检查投标文件内容是否完整。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        session_id = await manager.create_and_run_session(
            messages=messages,
            model="deepseek-ai/DeepSeek-V3.2-Exp",
            description=description,
        )

        # 写入 model_session 字段
        bid_record = (
            db.query(BidRecord).filter(BidRecord.id == bid_record_id).first()
        )
        if not bid_record:
            return {
                "bid_record_id": bid_record_id,
                "supplier_id": supplier_id,
                "status": "failed",
                "error": "投标记录不存在",
            }

        bid_record.ai_preliminary_review_model_session = session_id
        db.commit()

        # 等待任务完成
        task_result = await _run_ai_preliminary_review_task(
            bid_record_id=bid_record_id,
            project_id=project_id,
            tender_file_id=tender_file_id,
            bid_file_id=bid_file_id,
            session_id=session_id,
        )

        if task_result.get("success"):
            return {
                "bid_record_id": bid_record_id,
                "supplier_id": supplier_id,
                "status": "success",
                "ai_preliminary_review": task_result["result"],
            }
        else:
            return {
                "bid_record_id": bid_record_id,
                "supplier_id": supplier_id,
                "status": "failed",
                "error": task_result.get("error", "未知错误"),
            }

    except Exception as e:
        logger.error(
            f"[批量AI初评] 处理投标记录 {bid_record_id} 失败: {str(e)}"
        )
        import traceback

        logger.error(
            f"[批量AI初评] 错误堆栈:\n{traceback.format_exc()}"
        )
        return {
            "bid_record_id": bid_record_id,
            "supplier_id": supplier_id,
            "status": "failed",
            "error": str(e),
        }
    finally:
        db.close()


async def _run_ai_preliminary_review_task(
    bid_record_id: int,
    project_id: int,
    tender_file_id: str,
    bid_file_id: str,
    session_id: str,
) -> dict:
    """
    在当前请求中执行 AI 初审任务：
    - 等待会话启动 & 完成
    - 解析大模型输出 JSON: {"reason": "...", "pass": true/false}
    - 写回 BidRecord.ai_preliminary_review / ai_preliminary_review_success
    - 无论成功或失败，最后都清空 ai_preliminary_review_model_session
    """
    from ...db import SessionLocal  # 避免循环依赖

    logger.info(
        f"[AI初审任务 {bid_record_id}] 开始执行，project_id={project_id}, "
        f"tender_file_id={tender_file_id}, bid_file_id={bid_file_id}, session_id={session_id}"
    )

    db = SessionLocal()
    try:
        bid_record = (
            db.query(BidRecord)
            .filter(BidRecord.id == bid_record_id)
            .first()
        )
        if not bid_record:
            logger.error(f"[AI初审任务 {bid_record_id}] 投标记录不存在")
            raise RuntimeError(f"投标记录不存在: {bid_record_id}")

        manager = get_manager()

        # 等待会话启动（最多 5 分钟）
        logger.info(f"[AI初审任务 {bid_record_id}] 等待会话启动: {session_id}")
        wait_count = 0
        max_wait_start = 300
        while wait_count < max_wait_start:
            try:
                session_status = manager.get_session_status(session_id)
                if session_status in [
                    SessionStatus.RUNNING,
                    SessionStatus.FINISHED,
                    SessionStatus.ERROR,
                ]:
                    logger.info(
                        f"[AI初审任务 {bid_record_id}] 会话已启动, 状态: {session_status}"
                    )
                    break
            except Exception:
                # 会话可能还未创建，继续等待
                pass
            await asyncio.sleep(1)
            wait_count += 1

        if wait_count >= max_wait_start:
            logger.error(f"[AI初审任务 {bid_record_id}] 会话启动超时")
            raise RuntimeError(f"会话启动超时: {session_id}")

        # 等待会话完成（最多 5 分钟）
        logger.info(f"[AI初审任务 {bid_record_id}] 等待会话完成: {session_id}")
        max_wait_time = 600
        wait_count = 0
        last_status = None

        while wait_count < max_wait_time:
            try:
                session_status = manager.get_session_status(session_id)
                if session_status != last_status:
                    logger.info(
                        f"[AI初审任务 {bid_record_id}] 会话状态变化: "
                        f"{last_status} -> {session_status}"
                    )
                    last_status = session_status

                if session_status == SessionStatus.FINISHED:
                    logger.info(f"[AI初审任务 {bid_record_id}] 会话已完成")
                    break
                if session_status == SessionStatus.ERROR:
                    logger.error(f"[AI初审任务 {bid_record_id}] 会话执行失败")
                    raise RuntimeError("会话执行失败")
            except Exception as e:
                logger.warning(
                    f"[AI初审任务 {bid_record_id}] 查询会话状态异常: {str(e)}"
                )

            await asyncio.sleep(1)
            wait_count += 1

        if wait_count >= max_wait_time:
            logger.error(f"[AI初审任务 {bid_record_id}] 会话完成超时")
            raise RuntimeError(f"会话完成超时: {session_id}")

        # 获取会话结果
        session = manager.get_session(session_id)
        if not session:
            logger.error(f"[AI初审任务 {bid_record_id}] 会话不存在: {session_id}")
            raise RuntimeError(f"会话不存在: {session_id}")

        # 根据会话类型提取文本内容
        from ...model_session.model_session_manager import (
            LiveSession,
            HistorySession,
        )

        if isinstance(session, LiveSession):
            response_content = session._extract_content()
        elif isinstance(session, HistorySession):
            response_content = session.content or ""
        else:
            response_content = getattr(session, "content", "") or ""

        if not response_content:
            logger.error(f"[AI初审任务 {bid_record_id}] 响应内容为空")
            raise RuntimeError("响应内容为空")

        logger.info(
            f"[AI初审任务 {bid_record_id}] 获取响应内容成功，长度: {len(response_content)}"
        )

        # 解析 JSON：期望 {"reason": "...", "pass": true/false}
        result_obj = None
        try:
            # 优先尝试整体解析
            result_obj = json.loads(response_content)
        except json.JSONDecodeError:
            # 简单兜底：截取第一对大括号再解析
            try:
                start = response_content.find("{")
                end = response_content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    snippet = response_content[start : end + 1]
                    result_obj = json.loads(snippet)
            except Exception as e:
                logger.error(
                    f"[AI初审任务 {bid_record_id}] JSON 解析失败: {str(e)}; "
                    f"content 前500字: {response_content[:500]}"
                )
                raise RuntimeError("无法解析大模型返回的 JSON") from e

        if not isinstance(result_obj, dict):
            raise RuntimeError("大模型返回格式错误：不是 JSON 对象")

        reason = str(result_obj.get("reason", "") or "").strip()
        pass_flag_raw = result_obj.get("pass")
        if isinstance(pass_flag_raw, bool):
            pass_flag = pass_flag_raw
        elif isinstance(pass_flag_raw, str):
            pass_flag = pass_flag_raw.strip().lower() in ["true", "yes", "通过"]
        else:
            pass_flag = False

        if not reason:
            reason = "模型未给出明确原因"

        ai_result = {"reason": reason, "pass": pass_flag}

        # 写回数据库
        bid_record.ai_preliminary_review = ai_result
        bid_record.ai_preliminary_review_success = pass_flag
        db.commit()
        db.refresh(bid_record)

        logger.info(
            f"[AI初审任务 {bid_record_id}] 写入 AI 初审结果成功: "
            f"pass={pass_flag}, reason={reason}"
        )

        return {"success": True, "result": ai_result}

    except Exception as e:
        logger.error(f"[AI初审任务 {bid_record_id}] 任务执行失败: {str(e)}")
        import traceback

        logger.error(
            f"[AI初审任务 {bid_record_id}] 错误堆栈:\n{traceback.format_exc()}"
        )
        return {"success": False, "error": str(e)}

    finally:
        # 无论成功失败，都清空 model_session 字段
        try:
            bid_record = (
                db.query(BidRecord)
                .filter(BidRecord.id == bid_record_id)
                .first()
            )
            if bid_record:
                bid_record.ai_preliminary_review_model_session = None
                db.commit()
                logger.info(
                    f"[AI初审任务 {bid_record_id}] 已清空 AI初审_model_session 字段"
                )
        except Exception as cleanup_error:
            logger.error(
                f"[AI初审任务 {bid_record_id}] 清空 AI初审_model_session 失败: "
                f"{str(cleanup_error)}"
            )
        db.close()


@router.post(
    "/ai-preliminary-review",
    summary="触发单个供应商投标记录的 AI 初审",
    description=(
        "输入项目 ID 和供应商 ID，检查前置条件（项目已有采购征询文件、投标文件存在、"
        "且当前没有 AI 初审/会话进行中），然后调用大模型对投标文件内容完整性进行检查，"
        "返回 {\"reason\": 原因, \"pass\": true/false}。"
    ),
)
async def ai_preliminary_review(
    request: Annotated[AiPreliminaryReviewRequest, ...],
    db: Session = Depends(get_db),
):
    """
    触发 AI 初审（同步等待结果）：

    1. 检查前置条件：
       - 项目存在，且已有采购征询文件（tender_document_file_id 不为空）
       - 投标记录存在，且有投标文件（bid_document_file_id 不为空）
       - 当前投标记录的 ai_preliminary_review、ai_preliminary_review_model_session 为空
    2. 构建 prompt，要求大模型输出 {"reason": "...", "pass": true/false}
    3. 使用 model_session_manager 创建会话，并等待执行完成
    4. 将结果写入投标记录，并清空 ai_preliminary_review_model_session 字段
    """
    project_id = request.project_id
    supplier_id = request.supplier_id

    # 1. 校验项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")

    if not project.tender_document_file_id:
        raise HTTPException(
            status_code=400,
            detail="项目尚未生成采购征询文件，无法进行 AI 初审",
        )

    # 2. 校验投标记录
    bid_record = (
        db.query(BidRecord)
        .filter(
            BidRecord.project_id == project_id,
            BidRecord.supplier_id == supplier_id,
        )
        .first()
    )
    if not bid_record:
        raise HTTPException(
            status_code=404,
            detail=f"投标记录（项目 ID {project_id}，供应商 ID {supplier_id}）不存在",
        )

    if not bid_record.bid_document_file_id:
        raise HTTPException(
            status_code=400,
            detail="该供应商尚无投标文件，无法进行 AI 初审",
        )

    if bid_record.ai_preliminary_review_model_session or bid_record.ai_preliminary_review:
        raise HTTPException(
            status_code=400,
            detail="该投标记录已存在 AI 初审结果或正在处理中，请勿重复触发",
        )

    # 3. 读取采购征询文件和投标文件内容（Markdown）
    tender_file = (
        db.query(File)
        .filter(File.file_id == project.tender_document_file_id)
        .first()
    )
    if not tender_file:
        raise HTTPException(
            status_code=404,
            detail=f"采购征询文件记录不存在: {project.tender_document_file_id}",
        )

    bid_file = (
        db.query(File)
        .filter(File.file_id == bid_record.bid_document_file_id)
        .first()
    )
    if not bid_file:
        raise HTTPException(
            status_code=404,
            detail=f"投标文件记录不存在: {bid_record.bid_document_file_id}",
        )

    tender_md = tender_file.read_content_as_mark_down(settings.data_folder) or ""
    bid_md = bid_file.read_content_as_mark_down(settings.data_folder) or ""

    if not tender_md:
        raise HTTPException(
            status_code=400,
            detail="采购征询文件无法读取内容，无法进行 AI 初审",
        )
    if not bid_md:
        raise HTTPException(
            status_code=400,
            detail="投标文件无法读取内容，无法进行 AI 初审",
        )

    # 限制长度，避免 token 过长
    max_len = 50000
    tender_md_limited = (
        tender_md[:max_len] + "...\n[内容已截断]" if len(tender_md) > max_len else tender_md
    )
    bid_md_limited = (
        bid_md[:max_len] + "...\n[内容已截断]" if len(bid_md) > max_len else bid_md
    )

    # 4. 构建 Prompt
    prompt = f"""你是一名资深的采购评审专家，现在需要从“内容完整性”的角度，
对某个供应商的投标文件进行快速“AI 初审”，只判断是否完整响应了采购征询文件中的要求，
不需要做技术优劣或商务优劣的评价。

请对比以下两部分内容：

【一、采购征询文件（节选）】
{tender_md_limited}

【二、该供应商的投标文件（节选）】
{bid_md_limited}

请你重点从以下方面判断投标文件是否“内容完整”：
- 是否逐条（或在逻辑上）覆盖了采购征询文件中的主要技术要求、商务条款和服务承诺
- 是否缺失关键章节或关键条款（例如：技术方案、报价说明、交付计划、售后服务等）
- 是否存在明显的空白、引用错误模板、与本项目无关的大段内容等情况

请综合上述情况，给出你的结论，并严格按照下面 JSON 格式输出（不要包含任何多余文字）：
{{
  "reason": "简要说明通过/不通过的理由，50~200字左右，必须是中文",
  "pass": true 或 false   // true 表示内容基本完整，可以进入后续人工评审；false 表示内容明显不完整
}}

注意：
- 一定要返回合法的 JSON 格式
- 不要在 JSON 外再添加其他解释或文字
"""

    # 5. 使用 model_session_manager 创建会话
    manager = get_manager()
    description = {
        "type": "ai_preliminary_review",
        "project_id": project_id,
        "supplier_id": supplier_id,
        "bid_record_id": bid_record.id,
        "tender_file_id": project.tender_document_file_id,
        "bid_file_id": bid_record.bid_document_file_id,
    }

    messages = [
        {
            "role": "system",
            "content": "你是一名严谨的采购评审专家，主要负责根据采购征询文件检查投标文件内容是否完整。",
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        session_id = await manager.create_and_run_session(
            messages=messages,
            model="deepseek-ai/DeepSeek-V3.2-Exp",
            description=description,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"创建 AI 初审会话失败: {str(e)}"
        )

    # 写入 model_session 字段
    bid_record.ai_preliminary_review_model_session = session_id
    db.commit()
    db.refresh(bid_record)

    logger.info(
        f"[AI初审触发] 已为投标记录 {bid_record.id} 创建会话: {session_id}, "
        f"project_id={project_id}, supplier_id={supplier_id}"
    )

    # 6. 在当前请求内等待任务结束并返回结果
    task_result = await _run_ai_preliminary_review_task(
        bid_record_id=bid_record.id,
        project_id=project_id,
        tender_file_id=project.tender_document_file_id,
        bid_file_id=bid_record.bid_document_file_id,
        session_id=session_id,
    )

    if task_result.get("success"):
        return {
            "project_id": project_id,
            "supplier_id": supplier_id,
            "bid_record_id": bid_record.id,
            "session_id": session_id,
            "ai_preliminary_review": task_result["result"],
        }

    # 失败时仍然返回错误信息，但前面 _run_ai_preliminary_review_task 已经负责清空 session 字段
    raise HTTPException(
        status_code=500,
        detail=f"AI 初审任务执行失败: {task_result.get('error', '未知错误')}",
    )


@router.post(
    "/ai-preliminary-review/all",
    summary="触发项目下所有供应商投标记录的 AI 初审",
    description=(
        "输入项目 ID，自动遍历该项目下的所有投标记录，对符合条件的记录逐一进行 AI 初审。"
        "返回每个供应商的执行结果（成功/失败/跳过原因）。"
    ),
)
async def ai_preliminary_review_all(
    request: Annotated[AiPreliminaryReviewAllRequest, ...],
    db: Session = Depends(get_db),
):
    """
    批量触发 AI 初审（同步串行执行）：

    - 仅对满足以下条件的投标记录执行：
        * 有投标文件（bid_document_file_id 不为空）
        * 当前 ai_preliminary_review、ai_preliminary_review_model_session 为空
    - 每条记录调用一次大模型，执行逻辑与单个供应商接口一致
    - 为避免接口过长时间阻塞，建议项目下供应商数量不要太多
    """
    project_id = request.project_id

    # 校验项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")

    if not project.tender_document_file_id:
        raise HTTPException(
            status_code=400,
            detail="项目尚未生成采购征询文件，无法进行 AI 初审",
        )

    # 查询该项目下所有投标记录
    bid_records = (
        db.query(BidRecord)
        .filter(BidRecord.project_id == project_id)
        .all()
    )

    if not bid_records:
        return {
            "project_id": project_id,
            "total": 0,
            "processed": 0,
            "results": [],
            "message": "该项目暂无投标记录",
        }

    results = []
    processed_count = 0

    for bid_record in bid_records:
        supplier_id = bid_record.supplier_id
        record_info = {
            "bid_record_id": bid_record.id,
            "project_id": project_id,
            "supplier_id": supplier_id,
        }

        # 过滤条件：必须有投标文件，且当前无 AI 初审结果和会话
        if not bid_record.bid_document_file_id:
            record_info.update(
                {
                    "status": "skipped",
                    "reason": "该投标记录没有投标文件",
                }
            )
            results.append(record_info)
            continue

        if bid_record.ai_preliminary_review or bid_record.ai_preliminary_review_model_session:
            record_info.update(
                {
                    "status": "skipped",
                    "reason": "已经存在 AI 初审结果或正在处理中",
                }
            )
            results.append(record_info)
            continue

        # 构造单条记录请求对象，复用单个接口逻辑
        single_req = AiPreliminaryReviewRequest(
            project_id=project_id,
            supplier_id=supplier_id,
        )

        try:
            processed_count += 1
            single_result = await ai_preliminary_review(single_req, db)
            record_info.update(
                {
                    "status": "success",
                    "ai_preliminary_review": single_result.get(
                        "ai_preliminary_review"
                    ),
                }
            )
        except HTTPException as e:
            # 保留业务错误信息
            record_info.update(
                {
                    "status": "failed",
                    "error": str(e.detail),
                }
            )
        except Exception as e:
            record_info.update(
                {
                    "status": "failed",
                    "error": str(e),
                }
            )

        results.append(record_info)

    return {
        "project_id": project_id,
        "total": len(bid_records),
        "processed": processed_count,
        "results": results,
    }


async def _batch_ai_preliminary_review_task(project_id: int):
    """
    后台任务：批量处理项目下所有供应商的AI初评
    
    在后台异步执行，不阻塞请求
    """
    from ...db import SessionLocal

    logger.info(f"[批量AI初评任务] 开始处理项目 {project_id}")
    db = SessionLocal()
    try:
        # 重新查询项目信息
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"[批量AI初评任务] 项目不存在: {project_id}")
            return

        if not project.tender_document_file_id:
            logger.error(
                f"[批量AI初评任务] 项目尚未生成采购征询文件: {project_id}"
            )
            return

        # 查询所有投标记录
        bid_records = (
            db.query(BidRecord)
            .filter(BidRecord.project_id == project_id)
            .all()
        )

        if not bid_records:
            logger.info(f"[批量AI初评任务] 项目 {project_id} 暂无投标记录")
            return

        logger.info(
            f"[批量AI初评任务] 项目 {project_id} 共有 {len(bid_records)} 条投标记录"
        )

        # 筛选需要处理的记录
        tasks = []
        for bid_record in bid_records:
            # 过滤条件：必须有投标文件，且当前无 AI 初审结果和会话
            if not bid_record.bid_document_file_id:
                logger.info(
                    f"[批量AI初评任务] 跳过投标记录 {bid_record.id}: 没有投标文件"
                )
                continue

            if (
                bid_record.ai_preliminary_review
                or bid_record.ai_preliminary_review_model_session
            ):
                logger.info(
                    f"[批量AI初评任务] 跳过投标记录 {bid_record.id}: "
                    "已存在AI初评结果或正在处理中"
                )
                continue

            # 创建任务
            tasks.append(
                _process_single_bid_record_async(
                    bid_record_id=bid_record.id,
                    project_id=project_id,
                    supplier_id=bid_record.supplier_id,
                    tender_file_id=project.tender_document_file_id,
                    bid_file_id=bid_record.bid_document_file_id,
                )
            )

        logger.info(
            f"[批量AI初评任务] 项目 {project_id} 共有 {len(tasks)} 条记录需要处理"
        )

        # 串行执行任务（避免并发过多导致资源耗尽）
        for task in tasks:
            try:
                result = await task
                logger.info(
                    f"[批量AI初评任务] 投标记录 {result.get('bid_record_id')} "
                    f"处理完成，状态: {result.get('status')}"
                )
            except Exception as e:
                logger.error(
                    f"[批量AI初评任务] 处理任务失败: {str(e)}"
                )

        logger.info(f"[批量AI初评任务] 项目 {project_id} 处理完成")

    except Exception as e:
        logger.error(f"[批量AI初评任务] 任务执行失败: {str(e)}")
        import traceback

        logger.error(
            f"[批量AI初评任务] 错误堆栈:\n{traceback.format_exc()}"
        )
    finally:
        db.close()


@router.post(
    "/ai-preliminary-review/all/async",
    summary="一键触发项目下所有供应商的 AI 初评（异步后台任务）",
    description=(
        "输入项目 ID，立即返回任务已启动的响应，然后在后台异步处理该项目下所有符合条件的投标记录。"
        "使用 /ai-preliminary-review/all/{project_id}/status 接口查询处理进度和结果。"
    ),
)
async def ai_preliminary_review_all_async(
    request: Annotated[AiPreliminaryReviewAllRequest, ...],
    db: Session = Depends(get_db),
):
    """
    一键触发批量 AI 初评（异步后台任务）：
    
    - 立即返回响应，不阻塞请求
    - 在后台异步处理所有符合条件的投标记录
    - 仅处理满足以下条件的记录：
        * 有投标文件（bid_document_file_id 不为空）
        * 当前 ai_preliminary_review、ai_preliminary_review_model_session 为空
    - 使用状态查询接口获取处理进度和结果
    """
    project_id = request.project_id

    # 校验项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")

    if not project.tender_document_file_id:
        raise HTTPException(
            status_code=400,
            detail="项目尚未生成采购征询文件，无法进行 AI 初审",
        )

    # 查询需要处理的记录数量
    bid_records = (
        db.query(BidRecord)
        .filter(BidRecord.project_id == project_id)
        .all()
    )

    total_count = len(bid_records)
    pending_count = 0

    for bid_record in bid_records:
        if (
            bid_record.bid_document_file_id
            and not bid_record.ai_preliminary_review
            and not bid_record.ai_preliminary_review_model_session
        ):
            pending_count += 1

    # 启动后台任务
    async def background_task():
        try:
            await _batch_ai_preliminary_review_task(project_id)
        except Exception as e:
            logger.error(
                f"[一键AI初评] 后台任务执行失败: {str(e)}"
            )
            import traceback

            logger.error(
                f"[一键AI初评] 错误堆栈:\n{traceback.format_exc()}"
            )

    asyncio.create_task(background_task())
    logger.info(
        f"[一键AI初评] 已为项目 {project_id} 启动后台任务，"
        f"待处理记录数: {pending_count}"
    )

    return {
        "project_id": project_id,
        "total": total_count,
        "pending": pending_count,
        "message": "AI初评任务已启动，正在后台处理中，请使用状态查询接口查看进度",
    }


@router.get(
    "/ai-preliminary-review/all/{project_id}/status",
    summary="查询项目下所有供应商 AI 初评的状态和进度",
    description=(
        "查询指定项目下所有投标记录的AI初评状态，包括："
        "- success: 已完成AI初评的记录列表"
        "- failed: AI初评失败的记录列表"
        "- processing: 正在处理中的记录列表"
        "- pending: 待处理的记录列表"
    ),
)
async def get_ai_preliminary_review_all_status(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    查询批量AI初评状态
    
    返回该项目的所有投标记录及其AI初评状态：
    - success: 已完成AI初评的记录列表
    - failed: AI初评失败的记录列表
    - processing: 正在处理中的记录列表
    - pending: 待处理的记录列表
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")

    # 查询该项目的所有投标记录
    bid_records = (
        db.query(BidRecord).filter(BidRecord.project_id == project_id).all()
    )

    success_list = []
    failed_list = []
    processing_list = []
    pending_list = []

    manager = get_manager()

    for bid_record in bid_records:
        # 获取供应商信息
        supplier_name = None
        if bid_record.supplier_id:
            from ...db import Supplier

            supplier = (
                db.query(Supplier)
                .filter(Supplier.id == bid_record.supplier_id)
                .first()
            )
            if supplier:
                supplier_name = supplier.name

        record_info = {
            "bid_record_id": bid_record.id,
            "supplier_id": bid_record.supplier_id,
            "supplier_name": supplier_name,
            "has_bid_file": bool(bid_record.bid_document_file_id),
        }

        # 判断状态
        if bid_record.ai_preliminary_review:
            # 已有AI初评结果
            record_info.update(
                {
                    "ai_preliminary_review": bid_record.ai_preliminary_review,
                    "ai_preliminary_review_success": bid_record.ai_preliminary_review_success,
                }
            )
            success_list.append(record_info)
        elif bid_record.ai_preliminary_review_model_session:
            # 有会话ID，检查会话状态
            try:
                session_status = manager.get_session_status(
                    bid_record.ai_preliminary_review_model_session
                )

                if session_status == SessionStatus.FINISHED:
                    # 会话已完成，但可能结果还未写入数据库（短暂状态）
                    # 或者写入失败
                    processing_list.append(
                        {
                            **record_info,
                            "session_status": session_status.value,
                            "note": "会话已完成，等待结果写入",
                        }
                    )
                elif session_status == SessionStatus.ERROR:
                    # 会话执行失败
                    failed_list.append(
                        {
                            **record_info,
                            "error": "会话执行失败",
                            "session_status": session_status.value,
                        }
                    )
                else:
                    # 正在处理中
                    processing_list.append(
                        {
                            **record_info,
                            "session_status": session_status.value,
                        }
                    )
            except Exception as e:
                # 无法获取会话状态，可能已过期或不存在
                failed_list.append(
                    {
                        **record_info,
                        "error": f"无法获取会话状态: {str(e)}",
                        "session_status": "unknown",
                    }
                )
        else:
            # 没有会话ID，判断是否待处理
            if bid_record.bid_document_file_id:
                pending_list.append(
                    {
                        **record_info,
                        "reason": "有投标文件但尚未开始AI初评",
                    }
                )
            else:
                # 没有投标文件，跳过
                pass

    return {
        "project_id": project_id,
        "total": len(bid_records),
        "success_count": len(success_list),
        "failed_count": len(failed_list),
        "processing_count": len(processing_list),
        "pending_count": len(pending_list),
        "success": success_list,
        "failed": failed_list,
        "processing": processing_list,
        "pending": pending_list,
    }


@router.get(
    "/ai-preliminary-review/{project_id}/{supplier_id}/stream",
    summary="获取单个供应商 AI 初审的流式响应",
    description=(
        "根据投标记录上的 ai_preliminary_review_model_session，从 model_manager 中获取会话，"
        "使用 get_response 进行 SSE 流式返回，用于前端实时查看大模型推理过程。"
    ),
)
async def get_ai_preliminary_review_stream(
    project_id: int,
    supplier_id: int,
    db: Session = Depends(get_db),
):
    """
    获取某项目下某供应商投标记录的 AI 初审结果 / 流式响应。
    
    优先级：
    1. 如果投标记录中已有 ai_preliminary_review（JSON），直接返回该结果（普通 JSON 响应）；
    2. 否则，如果仍有 ai_preliminary_review_model_session，走 SSE 流式返回模型推理过程。
    """
    from fastapi.responses import StreamingResponse, JSONResponse
    import json

    # 查询投标记录
    bid_record = (
        db.query(BidRecord)
        .filter(
            BidRecord.project_id == project_id,
            BidRecord.supplier_id == supplier_id,
        )
        .first()
    )

    if not bid_record:
        raise HTTPException(
            status_code=404,
            detail=f"投标记录（项目 ID {project_id}，供应商 ID {supplier_id}）不存在",
        )
    
    # 1) 如果已经有 AI 初审结果（JSON），直接返回普通 JSON
    if bid_record.ai_preliminary_review:
        return JSONResponse(
            content={
                "project_id": project_id,
                "supplier_id": supplier_id,
                "bid_record_id": bid_record.id,
                "ai_preliminary_review": bid_record.ai_preliminary_review,
            }
        )
    
    # 2) 否则如果没有 session_id，无法获取流式响应
    if not bid_record.ai_preliminary_review_model_session:
        raise HTTPException(
            status_code=400,
            detail="无法获取流式响应：AI初审会话ID不存在或已被清空，且当前没有AI初审结果",
        )

    session_id = bid_record.ai_preliminary_review_model_session
    manager = get_manager()

    # 从 model_manager 中获取会话
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    async def generate_stream():
        try:
            # 发送初始状态信息
            yield f"data: {json.dumps({'type': 'status', 'session_id': session_id})}\n\n"

            # 使用 get_response 进行流式返回
            async for chunk in session.get_response():
                if chunk.delta_content:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.delta_content})}\n\n"

            # 结束时再尝试发送一次状态信息（可能会话已被转为 HistorySession）
            try:
                session_status = manager.get_session_status(session_id)
                status_value = getattr(session_status, 'value', str(session_status))
            except Exception:
                status_value = "unknown"

            yield f"data: {json.dumps({'type': 'status', 'status': status_value})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
    )


