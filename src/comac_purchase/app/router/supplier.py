"""
供应商相关的 API 路由
"""
import asyncio
import uuid
import logging
from pathlib import Path
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, Form, HTTPException, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...config import settings
from ...db import Supplier, BidRecord, File as FileModel, Project, get_db
from ...model_session.model_session_manager import get_manager, SessionStatus

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/supplier", tags=["supplier"])


class SupplierUpdateRequest(BaseModel):
    """供应商更新请求模型"""
    name: Optional[str] = None
    registration_number: Optional[str] = None


@router.post("/", summary="创建供应商", description="创建新供应商")
async def create_supplier(
    name: Annotated[str, Form(..., description="供应商名称")],
    registration_number: Annotated[str, Form(..., description="社会信用代码")],
    db: Session = Depends(get_db)
):
    """
    创建新供应商
    
    - **name**: 供应商名称
    - **registration_number**: 社会信用代码（必须唯一）
    
    返回创建的供应商信息
    """
    try:
        # 创建供应商记录
        supplier = Supplier(
            name=name,
            registration_number=registration_number
        )
        db.add(supplier)
        
        # 提交事务
        db.commit()
        db.refresh(supplier)
        
        return {
            "id": supplier.id,
            "name": supplier.name,
            "registration_number": supplier.registration_number
        }
    
    except IntegrityError as e:
        db.rollback()
        # 检查是否是唯一性约束错误
        if "UNIQUE constraint failed" in str(e) or "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"社会信用代码 '{registration_number}' 已存在，不能重复创建"
            )
        raise HTTPException(status_code=500, detail=f"创建供应商失败: {str(e)}")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建供应商失败: {str(e)}")


@router.patch("/{supplier_id}", summary="修改供应商字段", description="修改供应商的部分字段")
async def update_supplier(
    supplier_id: int,
    update_data: SupplierUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    修改供应商字段
    
    - **supplier_id**: 供应商ID
    - **update_data**: 要更新的字段（可选字段，只更新提供的字段）
        - name: 供应商名称
        - registration_number: 社会信用代码（必须唯一）
    
    返回更新后的供应商信息
    """
    # 查询供应商是否存在
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"供应商 ID {supplier_id} 不存在")
    
    try:
        # 更新提供的字段
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # 如果更新了 registration_number，检查是否与其他供应商重复
        if "registration_number" in update_dict:
            existing_supplier = db.query(Supplier).filter(
                Supplier.registration_number == update_dict["registration_number"],
                Supplier.id != supplier_id
            ).first()
            if existing_supplier:
                raise HTTPException(
                    status_code=400,
                    detail=f"社会信用代码 '{update_dict['registration_number']}' 已被其他供应商使用"
                )
        
        # 更新字段
        for field, value in update_dict.items():
            setattr(supplier, field, value)
        
        # 提交事务
        db.commit()
        db.refresh(supplier)
        
        return {
            "id": supplier.id,
            "name": supplier.name,
            "registration_number": supplier.registration_number
        }
    
    except HTTPException:
        db.rollback()
        raise
    
    except IntegrityError as e:
        db.rollback()
        # 检查是否是唯一性约束错误
        if "UNIQUE constraint failed" in str(e) or "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"社会信用代码已存在，不能重复使用"
            )
        raise HTTPException(status_code=500, detail=f"修改供应商失败: {str(e)}")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改供应商失败: {str(e)}")


async def _identify_supplier_task(
    bid_record_id: int,
    file_id: str,
    session_id: str
):
    """后台任务：识别供应商信息（超时1分钟）"""
    from ...db import SessionLocal
    
    logger.info(f"[身份识别任务 {bid_record_id}] 开始执行识别任务，会话ID: {session_id}")
    logger.info(f"[身份识别任务 {bid_record_id}] 文件ID: {file_id}")
    
    # 创建新的数据库会话
    db = SessionLocal()
    try:
        # 获取投标记录
        bid_record = db.query(BidRecord).filter(BidRecord.id == bid_record_id).first()
        if not bid_record:
            logger.error(f"[身份识别任务 {bid_record_id}] 投标记录不存在")
            raise RuntimeError(f"投标记录不存在: {bid_record_id}")
        
        logger.info(f"[身份识别任务 {bid_record_id}] 获取投标记录成功，项目ID: {bid_record.project_id}")
        
        # 重新查询文件（使用新的数据库会话）
        file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        
        if not file_record:
            logger.error(f"[身份识别任务 {bid_record_id}] 文件记录不存在，file_id: {file_id}")
            raise RuntimeError("文件不存在")
        
        logger.info(f"[身份识别任务 {bid_record_id}] 文件记录查询成功 - 原始文件名: {file_record.origin_name}, 保存文件名: {file_record.file_name}, file_id: {file_id}")
        
        # 读取文件内容
        files_folder = Path(settings.data_folder) / "files"
        file_path = files_folder / file_record.file_name
        
        logger.info(f"[身份识别任务 {bid_record_id}] 文件路径: {file_path}, 文件是否存在: {file_path.exists()}")
        
        if not file_path.exists():
            logger.error(f"[身份识别任务 {bid_record_id}] 物理文件不存在: {file_path}")
            raise FileNotFoundError("文件不存在")
        
        logger.info(f"[身份识别任务 {bid_record_id}] 物理文件验证成功，文件大小: {file_path.stat().st_size} 字节")
        
        # 读取文件内容为 Markdown
        file_content = file_record.read_content_as_mark_down(settings.data_folder)
        if not file_content:
            logger.error(f"[身份识别任务 {bid_record_id}] 无法读取文件内容")
            raise RuntimeError("无法读取文件内容")
        
        logger.info(f"[身份识别任务 {bid_record_id}] 文件内容读取成功，长度: {len(file_content)} 字符, 前200字符: {file_content[:200]}")
        
        # 使用 model_session 识别供应商信息
        manager = get_manager()
        
        # 等待会话启动（最多等待20分钟）
        logger.info(f"[身份识别任务 {bid_record_id}] 等待会话启动: {session_id}")
        wait_count = 0
        max_wait_start = 1200  # 最多等待20分钟让会话启动
        while wait_count < max_wait_start:
            try:
                session_status = manager.get_session_status(session_id)
                if session_status in [SessionStatus.RUNNING, SessionStatus.FINISHED, SessionStatus.ERROR]:
                    logger.info(f"[身份识别任务 {bid_record_id}] 会话已启动，状态: {session_status}")
                    break
            except Exception as e:
                # 会话可能还未创建，继续等待
                pass
            await asyncio.sleep(1)
            wait_count += 1
        
        if wait_count >= max_wait_start:
            logger.error(f"[身份识别任务 {bid_record_id}] 会话启动超时")
            raise RuntimeError(f"会话启动超时: {session_id}")
        
        # 等待会话完成，添加超时机制（最多等待20分钟）
        logger.info(f"[身份识别任务 {bid_record_id}] 等待会话完成: {session_id}")
        max_wait_time = 60  # 1分钟
        wait_count = 0
        
        while wait_count < max_wait_time:
            try:
                session_status = manager.get_session_status(session_id)
                if session_status == SessionStatus.FINISHED:
                    logger.info(f"[身份识别任务 {bid_record_id}] 会话已完成")
                    break
                elif session_status == SessionStatus.ERROR:
                    logger.error(f"[身份识别任务 {bid_record_id}] 会话执行失败")
                    raise RuntimeError("会话执行失败")
            except Exception as e:
                logger.warning(f"[身份识别任务 {bid_record_id}] 查询会话状态异常: {str(e)}")
            
            await asyncio.sleep(1)
            wait_count += 1
        
        if wait_count >= max_wait_time:
            logger.error(f"[身份识别任务 {bid_record_id}] 会话完成超时")
            raise RuntimeError(f"会话完成超时: {session_id}")
        
        # 获取会话结果
        session = manager.get_session(session_id)
        if not session:
            logger.error(f"[身份识别任务 {bid_record_id}] 会话不存在: {session_id}")
            raise RuntimeError(f"会话不存在: {session_id}")
        
        # 提取响应内容（根据会话类型选择不同的方法）
        from ...model_session.model_session_manager import LiveSession, HistorySession
        
        if isinstance(session, LiveSession):
            # LiveSession 使用 _extract_content() 方法
            response_content = session._extract_content()
        elif isinstance(session, HistorySession):
            # HistorySession 直接使用 content 属性
            response_content = session.content or ''
        else:
            # 兼容其他情况，尝试使用 content 属性
            response_content = getattr(session, 'content', '') or ''
        
        if not response_content:
            logger.error(f"[身份识别任务 {bid_record_id}] 响应内容为空")
            raise RuntimeError("响应内容为空")
        
        logger.info(f"[身份识别任务 {bid_record_id}] 获取响应内容，长度: {len(response_content)}")
        
        # 解析响应内容，提取供应商名称和社会信用代码
        # 期望格式：JSON 格式 {"name": "供应商名称", "registration_number": "社会信用代码"}
        import json
        import re
        
        supplier_name = ''
        registration_number = ''
        
        # 尝试提取 JSON（支持多行和嵌套）
        # 先尝试找到 JSON 代码块
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_block_match:
            try:
                supplier_info = json.loads(json_block_match.group(1))
                supplier_name = supplier_info.get('name', '').strip()
                registration_number = supplier_info.get('registration_number', '').strip()
            except json.JSONDecodeError:
                logger.warning(f"[身份识别任务 {bid_record_id}] JSON 代码块解析失败，尝试其他方式")
        
        # 如果还没找到，尝试直接匹配 JSON 对象
        if not supplier_name or not registration_number:
            json_match = re.search(r'\{[^{}]*"name"\s*:\s*"[^"]*"[^{}]*"registration_number"\s*:\s*"[^"]*"[^{}]*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    supplier_info = json.loads(json_match.group())
                    supplier_name = supplier_info.get('name', '').strip()
                    registration_number = supplier_info.get('registration_number', '').strip()
                except json.JSONDecodeError:
                    logger.warning(f"[身份识别任务 {bid_record_id}] JSON 解析失败，尝试其他方式提取")
        
        # 如果还没找到，尝试从文本中提取
        if not supplier_name or not registration_number:
            name_match = re.search(r'(?:供应商名称|名称|公司名称)[:：]\s*([^\n]+)', response_content)
            reg_match = re.search(r'(?:社会信用代码|信用代码|统一社会信用代码)[:：]\s*([A-Z0-9]{18})', response_content)
            
            supplier_name = name_match.group(1).strip() if name_match else supplier_name
            registration_number = reg_match.group(1).strip() if reg_match else registration_number
        
        if not supplier_name or not registration_number:
            logger.error(f"[身份识别任务 {bid_record_id}] 未能提取供应商信息 - 名称: {supplier_name}, 代码: {registration_number}")
            logger.error(f"[身份识别任务 {bid_record_id}] 响应内容: {response_content[:500]}")
            raise RuntimeError("未能提取供应商信息")
        
        logger.info(f"[身份识别任务 {bid_record_id}] 提取供应商信息成功 - 名称: {supplier_name}, 代码: {registration_number}")
        
        # 查找或创建供应商
        supplier = db.query(Supplier).filter(Supplier.registration_number == registration_number).first()
        if supplier:
            logger.info(f"[身份识别任务 {bid_record_id}] 供应商已存在，ID: {supplier.id}")
            supplier_id = supplier.id
        else:
            # 创建新供应商
            supplier = Supplier(
                name=supplier_name,
                registration_number=registration_number
            )
            db.add(supplier)
            db.flush()  # 刷新以获取供应商ID
            supplier_id = supplier.id
            logger.info(f"[身份识别任务 {bid_record_id}] 创建新供应商，ID: {supplier_id}")
        
        # 更新投标记录的供应商ID
        bid_record.supplier_id = supplier_id
        # 清空身份识别_model_session（任务完成）
        bid_record.identity_recognition_model_session = None
        db.commit()
        db.refresh(bid_record)
        logger.info(f"[身份识别任务 {bid_record_id}] 投标记录已更新供应商ID: {supplier_id}，已清空会话ID")
        
        # 返回成功结果
        return {
            "success": True,
            "bid_record_id": bid_record_id,
            "file_id": file_id,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "registration_number": registration_number,
            "message": "供应商识别成功"
        }
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"[身份识别任务 {bid_record_id}] 任务执行失败: {error_message}")
        import traceback
        logger.error(f"[身份识别任务 {bid_record_id}] 错误堆栈:\n{traceback.format_exc()}")
        
        # 失败后清空身份识别_model_session
        try:
            bid_record = db.query(BidRecord).filter(BidRecord.id == bid_record_id).first()
            if bid_record:
                bid_record.identity_recognition_model_session = None
                db.commit()
                logger.info(f"[身份识别任务 {bid_record_id}] 任务失败，已清空会话ID")
        except Exception as cleanup_error:
            logger.error(f"[身份识别任务 {bid_record_id}] 清空会话ID失败: {str(cleanup_error)}")
        
        # 返回失败结果
        return {
            "success": False,
            "bid_record_id": bid_record_id,
            "file_id": file_id,
            "error": error_message,
            "message": f"供应商识别失败: {error_message}"
        }
    finally:
        db.close()


@router.post("/batch-import", summary="批量导入供应商", description="上传多个投标文件，自动识别供应商信息并创建投标记录")
async def batch_import_suppliers(
    project_id: Annotated[int, Form(..., description="项目ID")],
    files: Annotated[List[UploadFile], File(..., description="投标文件列表（多个文件）")],
    db: Session = Depends(get_db)
):
    """
    批量导入供应商
    
    - **project_id**: 项目ID（必填）
    - **files**: 投标文件列表（多个文件，必须是 Word 文档 .doc 或 .docx）
    
    流程：
    1. 为每个文件创建投标记录（supplier_id 为空）
    2. 为每个文件启动异步 LLM 任务识别供应商信息
    3. 识别完成后自动创建供应商并更新投标记录
    
    返回创建的投标记录列表和任务信息
    """
    try:
        # 验证项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
        
        if not files:
            raise HTTPException(status_code=400, detail="至少需要上传一个文件")
        
        # 记录接收到的文件数量
        logger.info(f"[批量导入] 接收到 {len(files)} 个文件")
        for idx, file in enumerate(files):
            logger.info(f"[批量导入] 文件 {idx + 1}: {file.filename if file.filename else '未命名'}")
        
        # 确保文件存储目录存在
        files_folder = Path(settings.data_folder) / "files"
        files_folder.mkdir(parents=True, exist_ok=True)
        
        results = []
        tasks_to_start = []  # 保存待启动的任务信息
        
        # 第一步：创建和文件相同数量的投标记录
        for file in files:
            if not file.filename:
                continue
            
            # 验证文件类型必须是 Word 文档
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.doc', '.docx']:
                logger.warning(f"跳过非 Word 文件: {file.filename}")
                results.append({
                    "file_name": file.filename,
                    "status": "skipped",
                    "message": f"文件必须是 Word 文档格式（.doc 或 .docx），当前文件格式：{file_ext}"
                })
                continue
            
            # 生成文件 ID 和文件名
            file_id = str(uuid.uuid4())
            file_name = str(uuid.uuid4())
            
            logger.info(f"[批量导入] 处理文件: {file.filename}, 文件ID: {file_id}, 保存文件名: {file_name}")
            
            # 保存文件到磁盘
            file_path = files_folder / file_name
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            logger.info(f"[批量导入] 文件已保存: {file.filename}, 文件大小: {len(content)} 字节, 路径: {file_path}")
            
            # 检查是否已存在相同原始文件名称的投标记录（同一项目的同一文件）
            existing_bid = db.query(BidRecord).join(
                FileModel, BidRecord.bid_document_file_id == FileModel.file_id
            ).filter(
                BidRecord.project_id == project_id,
                FileModel.origin_name == file.filename
            ).first()
            
            if existing_bid:
                logger.warning(f"投标记录已存在: 项目ID {project_id}, 文件名称 {file.filename}")
                results.append({
                    "file_name": file.filename,
                    "status": "skipped",
                    "message": f"该文件 '{file.filename}' 的投标记录已存在"
                })
                continue
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=file.filename,
                file_name=file_name
            )
            db.add(file_record)
            db.flush()  # 刷新以获取文件记录
            
            # 创建投标记录（supplier_id 为空）
            bid_record = BidRecord(
                project_id=project_id,
                supplier_id=None,
                bid_document_file_id=file_id
            )
            db.add(bid_record)
            db.flush()  # 刷新以获取投标记录ID
            bid_record_id = bid_record.id
            
            # 读取文件内容为 Markdown
            file_content = file_record.read_content_as_mark_down(settings.data_folder)
            if not file_content:
                logger.warning(f"无法读取文件内容: {file.filename}")
                results.append({
                    "file_name": file.filename,
                    "bid_record_id": bid_record_id,
                    "status": "error",
                    "message": "无法读取文件内容"
                })
                continue
            
            logger.info(f"[批量导入] 文件内容读取成功: {file.filename}, 内容长度: {len(file_content)} 字符, 前100字符: {file_content[:100]}")
            
            # 保存任务信息，稍后启动异步任务
            tasks_to_start.append({
                "file": file,
                "file_id": file_id,
                "bid_record_id": bid_record_id,
                "file_content": file_content,
                "file_name": file.filename  # 保存原始文件名用于日志
            })
            
            results.append({
                "file_name": file.filename,
                "bid_record_id": bid_record_id,
                "file_id": file_id,
                "status": "created",
                "message": "投标记录已创建"
            })
        
        # 提交所有投标记录
        db.commit()
        logger.info(f"[批量导入] 第一步完成：已创建 {len(tasks_to_start)} 条投标记录")
        
        # 第二步：启动 N 个异步任务
        for task_info in tasks_to_start:
            file = task_info["file"]
            file_id = task_info["file_id"]
            bid_record_id = task_info["bid_record_id"]
            file_content = task_info["file_content"]
            file_name = task_info.get("file_name", file.filename)
            
            logger.info(f"[批量导入] 启动任务: 文件={file_name}, bid_record_id={bid_record_id}, file_id={file_id}, 内容长度={len(file_content)}")
            logger.info(f"[批量导入] 文件内容前200字符: {file_content[:200]}")
            
            # 限制文件内容长度，避免超出 token 限制
            file_content_limited = file_content[:10000] if len(file_content) > 10000 else file_content
            
            # 构建 prompt（使用当前循环的文件内容）
            prompt = f"""你是一位专业的文档分析专家。请从以下投标文件中提取供应商信息。

## 投标文件内容（文件名: {file_name}）

{file_content_limited}

## 任务要求

请仔细分析文档内容，提取以下信息：
1. **供应商名称**：公司的正式名称
2. **社会信用代码**：18位统一社会信用代码（格式：9位组织机构代码 + 9位统一社会信用代码）

## 输出格式

请以 JSON 格式输出结果，格式如下：
{{
    "name": "供应商名称",
    "registration_number": "18位社会信用代码"
}}

请确保：
- 供应商名称准确、完整
- 社会信用代码必须是18位，格式正确
- 如果无法找到信息，请返回空字符串

请直接输出 JSON 结果，不要包含其他说明文字。"""
            
            # 创建会话描述
            description = {
                "type": "identify_supplier",
                "bid_record_id": bid_record_id,
                "project_id": project_id,
                "file_id": file_id
            }
            
            # 创建并运行会话（异步任务）
            logger.info(f"[批量导入] 为文件 {file.filename} 创建并启动LLM会话")
            manager = get_manager()
            session_id = await manager.create_and_run_session(
                messages=[{
                    "role": "system",
                    "content": "你是一位专业的文档分析专家，擅长从投标文件中提取供应商信息。"
                }, {
                    "role": "user",
                    "content": prompt
                }],
                model="deepseek-ai/DeepSeek-V3.2-Exp",
                description=description
            )
            logger.info(f"[批量导入] LLM会话创建成功，会话ID: {session_id}")
            
            # 更新投标记录的 identity_recognition_model_session
            bid_record = db.query(BidRecord).filter(BidRecord.id == bid_record_id).first()
            if bid_record:
                bid_record.identity_recognition_model_session = session_id
                db.commit()
                logger.info(f"[批量导入] 投标记录已更新会话ID: {session_id}")
            
            # 启动后台任务（不等待完成，超时1分钟）
            # 注意：使用默认参数来捕获循环变量的值，避免闭包问题
            async def background_task(
                task_bid_record_id=bid_record_id,
                task_file_id=file_id,
                task_session_id=session_id,
                task_file_name=file_name
            ):
                from ...db import SessionLocal
                try:
                    logger.info(f"[批量导入] 启动后台任务处理文件: {task_file_name}, bid_record_id={task_bid_record_id}, file_id={task_file_id}")
                    await asyncio.wait_for(
                        _identify_supplier_task(
                            task_bid_record_id,
                            task_file_id,
                            task_session_id
                        ),
                        timeout=60.0  # 1分钟超时
                    )
                except asyncio.TimeoutError:
                    logger.error(f"[批量导入] 后台任务超时: {task_file_name}")
                    # 超时后清空 session_id
                    db_task = SessionLocal()
                    try:
                        bid_record_task = db_task.query(BidRecord).filter(BidRecord.id == task_bid_record_id).first()
                        if bid_record_task:
                            bid_record_task.identity_recognition_model_session = None
                            db_task.commit()
                            logger.info(f"[批量导入] 任务超时，已清空会话ID: {task_bid_record_id}")
                    finally:
                        db_task.close()
                except Exception as e:
                    logger.error(f"[批量导入] 后台任务执行失败: {task_file_name}, 错误: {str(e)}")
                    import traceback
                    logger.error(f"[批量导入] 后台任务错误堆栈:\n{traceback.format_exc()}")
                    # 失败后清空 session_id
                    db_task = SessionLocal()
                    try:
                        bid_record_task = db_task.query(BidRecord).filter(BidRecord.id == task_bid_record_id).first()
                        if bid_record_task:
                            bid_record_task.identity_recognition_model_session = None
                            db_task.commit()
                            logger.info(f"[批量导入] 任务失败，已清空会话ID: {task_bid_record_id}")
                    finally:
                        db_task.close()
            
            # 启动后台任务（不等待完成）
            asyncio.create_task(background_task())
            logger.info(f"[批量导入] 后台任务已启动: {file_name}")
            
            # 更新结果中的状态
            for result in results:
                if result.get("bid_record_id") == bid_record_id:
                    result["session_id"] = session_id
                    result["status"] = "processing"
                    result["message"] = "供应商识别任务已启动"
                    break
        
        return {
            "project_id": project_id,
            "total_files": len(files),
            "processed_files": len(results),
            "results": results,
            "message": f"已处理 {len(results)} 个文件，供应商识别任务已在后台启动"
        }
    
    except HTTPException:
        db.rollback()
        raise
    
    except Exception as e:
        db.rollback()
        logger.error(f"[批量导入] 批量导入失败: {str(e)}")
        import traceback
        logger.error(f"[批量导入] 错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")


@router.get("/batch-import/{project_id}/status", summary="查询批量导入状态", description="查询指定项目的批量导入任务状态")
async def get_batch_import_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    查询批量导入状态
    
    - **project_id**: 项目ID
    
    返回该项目的所有投标记录及其识别状态：
    - success: 识别成功的记录列表
    - failed: 识别失败的记录列表
    - processing: 正在处理中的记录列表
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    # 查询该项目的所有投标记录
    bid_records = db.query(BidRecord).filter(
        BidRecord.project_id == project_id
    ).all()
    
    success_list = []
    failed_list = []
    processing_list = []
    
    for bid_record in bid_records:
        # 获取文件信息
        file_info = None
        if bid_record.bid_document_file_id:
            file_record = db.query(FileModel).filter(
                FileModel.file_id == bid_record.bid_document_file_id
            ).first()
            if file_record:
                file_info = {
                    "file_id": file_record.file_id,
                    "file_name": file_record.origin_name
                }
        
        # 获取供应商信息
        supplier_info = None
        if bid_record.supplier_id:
            supplier = db.query(Supplier).filter(
                Supplier.id == bid_record.supplier_id
            ).first()
            if supplier:
                supplier_info = {
                    "supplier_id": supplier.id,
                    "name": supplier.name,
                    "registration_number": supplier.registration_number
                }
        
        record_info = {
            "bid_record_id": bid_record.id,
            "file": file_info,
            "supplier": supplier_info,
            "session_id": bid_record.identity_recognition_model_session,
            "submission_time": bid_record.submission_time.isoformat() if bid_record.submission_time else None
        }
        
        # 判断状态
        if bid_record.supplier_id:
            # 有供应商ID，说明识别成功
            success_list.append(record_info)
        elif bid_record.identity_recognition_model_session:
            # 有会话ID但没有供应商ID，检查会话状态
            try:
                manager = get_manager()
                session_status = manager.get_session_status(bid_record.identity_recognition_model_session)
                
                if session_status == SessionStatus.FINISHED:
                    # 会话已完成但没有供应商ID，说明识别失败
                    failed_list.append({
                        **record_info,
                        "error": "识别完成但未能提取供应商信息",
                        "session_status": session_status.value
                    })
                elif session_status == SessionStatus.ERROR:
                    # 会话执行失败
                    failed_list.append({
                        **record_info,
                        "error": "会话执行失败",
                        "session_status": session_status.value
                    })
                else:
                    # 正在处理中
                    processing_list.append({
                        **record_info,
                        "session_status": session_status.value
                    })
            except Exception as e:
                # 无法获取会话状态，可能已过期或不存在
                failed_list.append({
                    **record_info,
                    "error": f"无法获取会话状态: {str(e)}",
                    "session_status": "unknown"
                })
        else:
            # 没有会话ID，可能是手动创建的记录
            if bid_record.bid_document_file_id:
                # 有文件但没有会话，可能是未启动识别任务
                processing_list.append({
                    **record_info,
                    "error": "未启动识别任务"
                })
            else:
                # 既没有文件也没有会话
                failed_list.append({
                    **record_info,
                    "error": "缺少必要信息"
                })
    
    return {
        "project_id": project_id,
        "total": len(bid_records),
        "success_count": len(success_list),
        "failed_count": len(failed_list),
        "processing_count": len(processing_list),
        "success": success_list,
        "failed": failed_list,
        "processing": processing_list
    }

