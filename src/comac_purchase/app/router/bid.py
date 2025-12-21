"""
投标记录相关的 API 路由
"""
import uuid
from pathlib import Path
from typing import Annotated, Optional, Dict, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...config import settings
from ...db import BidRecord, File, Project, Supplier, get_db

router = APIRouter(prefix="/bid", tags=["bid"])


class BidRecordUpdateRequest(BaseModel):
    """投标记录更新请求模型"""
    bid_document_file_id: Optional[str] = None
    ai_preliminary_review: Optional[Dict[str, Any]] = None
    ai_preliminary_review_model_session: Optional[str] = None
    ai_preliminary_review_success: Optional[bool] = None
    preliminary_review: Optional[Dict[str, Any]] = None
    ai_evaluation: Optional[Dict[str, Any]] = None
    ai_evaluation_success: Optional[bool] = None


@router.post("/", summary="创建投标记录", description="创建新的投标记录，通过社会信用代码识别供应商")
async def create_bid(
    project_id: Annotated[int, Form(..., description="项目ID")],
    name: Annotated[str, Form(..., description="供应商名称")],
    registration_number: Annotated[str, Form(..., description="社会信用代码")],
    file: Annotated[Optional[UploadFile], File()] = None,
    db: Session = Depends(get_db)
):
    """
    创建新的投标记录
    
    - **project_id**: 项目ID（必填）
    - **name**: 供应商名称（必填，如果供应商已存在则使用已有名称）
    - **registration_number**: 社会信用代码（必填，用于识别供应商）
    - **file**: 投标文件（可选，如果上传必须是 Word 文档 .doc 或 .docx）
    
    如果库中已有该社会信用代码，则使用已有供应商；否则先创建供应商记录。
    返回创建的投标记录信息
    """
    try:
        # 验证项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
        
        # 根据社会信用代码查找或创建供应商
        supplier = db.query(Supplier).filter(Supplier.registration_number == registration_number).first()
        if supplier:
            # 如果供应商已存在，使用已有的供应商（忽略传入的名称）
            supplier_id = supplier.id
        else:
            # 如果供应商不存在，创建新供应商
            supplier = Supplier(
                name=name,
                registration_number=registration_number
            )
            db.add(supplier)
            db.flush()  # 刷新以获取供应商ID，但不提交事务
            supplier_id = supplier.id
        
        # 处理文件上传（如果提供了文件）
        file_id = None
        file_record = None
        if file and file.filename:
            # 验证文件类型必须是 Word 文档
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.doc', '.docx']:
                raise HTTPException(
                    status_code=400,
                    detail=f"投标文件必须是 Word 文档格式（.doc 或 .docx），当前文件格式：{file_ext}"
                )
            
            # 生成文件 ID 和文件名
            file_id = str(uuid.uuid4())
            file_name = str(uuid.uuid4())
            
            # 确保文件存储目录存在
            files_folder = Path(settings.data_folder) / "files"
            files_folder.mkdir(parents=True, exist_ok=True)
            
            # 保存文件到磁盘
            file_path = files_folder / file_name
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # 创建文件记录
            file_record = File(
                file_id=file_id,
                origin_name=file.filename,
                file_name=file_name
            )
            db.add(file_record)
        
        # 创建投标记录
        bid_record = BidRecord(
            project_id=project_id,
            supplier_id=supplier_id,
            bid_document_file_id=file_id
        )
        db.add(bid_record)
        
        # 提交事务
        db.commit()
        db.refresh(bid_record)
        db.refresh(supplier)  # 刷新供应商信息
        if file_record:
            db.refresh(file_record)
        
        # 构建返回结果
        result = {
            "project_id": bid_record.project_id,
            "supplier_id": bid_record.supplier_id,
            "bid_document_file_id": bid_record.bid_document_file_id,
            "submission_time": bid_record.submission_time.isoformat() if bid_record.submission_time else None,
            "project": {
                "id": project.id,
                "name": project.name
            },
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "registration_number": supplier.registration_number
            }
        }
        
        if file_record:
            result["file"] = {
                "file_id": file_record.file_id,
                "origin_name": file_record.origin_name,
                "file_name": file_record.file_name
            }
        
        return result
    
    except HTTPException:
        # 重新抛出 HTTP 异常
        db.rollback()
        raise
    
    except IntegrityError as e:
        db.rollback()
        # 检查是否是唯一性约束错误
        error_str = str(e).lower()
        if "unique constraint failed" in error_str or "unique constraint" in error_str:
            # 可能是投标记录的唯一性约束（同一项目和供应商组合已存在）
            # 或者是供应商的社会信用代码唯一性约束
            if "uq_project_supplier" in error_str or "project_id" in error_str:
                raise HTTPException(
                    status_code=400,
                    detail=f"项目 ID {project_id} 和社会信用代码 '{registration_number}' 的投标记录已存在，不能重复创建"
                )
            elif "registration_number" in error_str or "suppliers" in error_str:
                raise HTTPException(
                    status_code=400,
                    detail=f"社会信用代码 '{registration_number}' 已存在，但查询时未找到，可能存在数据不一致"
                )
        raise HTTPException(status_code=500, detail=f"创建投标记录失败: {str(e)}")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建投标记录失败: {str(e)}")


@router.get("/", summary="获取投标记录列表", description="根据项目ID获取投标记录列表（供应商列表）")
async def get_bid_records(
    project_id: Annotated[int, Query(..., description="项目ID")],
    db: Session = Depends(get_db)
):
    """
    获取项目的投标记录列表（即该项目的供应商列表）
    
    - **project_id**: 项目ID（必填，查询参数）
    
    返回投标记录列表，每个记录包含：
    - project_id: 项目ID
    - supplier_id: 供应商ID
    - supplier: 供应商信息（id, name, registration_number）
    - bid_document_file_id: 投标文件ID（如果有）
    - submission_time: 提交时间
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    # 查询该项目的所有投标记录
    bid_records = db.query(BidRecord).filter(
        BidRecord.project_id == project_id
    ).all()
    
    result = []
    for bid_record in bid_records:
        # 查询供应商信息（可能为空）
        supplier = None
        if bid_record.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == bid_record.supplier_id).first()
        
        # 查询投标文件信息
        bid_file = None
        if bid_record.bid_document_file_id:
            bid_file_record = db.query(File).filter(File.file_id == bid_record.bid_document_file_id).first()
            if bid_file_record:
                bid_file = {
                    "file_id": bid_file_record.file_id,
                    "file_name": bid_file_record.origin_name
                }
        
        # 构建返回数据
        record_data = {
            "bid_record_id": bid_record.id,
                "project_id": bid_record.project_id,
                "supplier_id": bid_record.supplier_id,
                "bid_document_file_id": bid_record.bid_document_file_id,
            "bid_file": bid_file,
            "ai_preliminary_review_success": bid_record.ai_preliminary_review_success,
            "ai_evaluation_success": bid_record.ai_evaluation_success,
            "submission_time": bid_record.submission_time.isoformat() if bid_record.submission_time else None
        }
        
        # 如果有供应商信息，添加供应商数据
        if supplier:
            record_data["supplier"] = {
                "id": supplier.id,
                "name": supplier.name,
                "registration_number": supplier.registration_number
            }
        else:
            # 如果没有供应商信息，使用"未知供应商"
            record_data["supplier"] = {
                "id": None,
                "name": "未知供应商",
                "registration_number": None
            }
        
        # 检查身份识别状态
        identity_status = None
        if bid_record.identity_recognition_model_session:
            try:
                from ...model_session.model_session_manager import get_manager, SessionStatus
                manager = get_manager()
                session_status = manager.get_session_status(bid_record.identity_recognition_model_session)
                if session_status == SessionStatus.RUNNING:
                    identity_status = "识别中"
                elif session_status == SessionStatus.FINISHED:
                    identity_status = "已完成"
                elif session_status == SessionStatus.ERROR:
                    identity_status = "识别失败"
                else:
                    identity_status = "待处理"
            except Exception:
                # 无法获取会话状态，可能已过期
                identity_status = None
        
        record_data["identity_status"] = identity_status
        record_data["identity_recognition_model_session"] = bid_record.identity_recognition_model_session
        
        result.append(record_data)
    
    return result


@router.patch("/{project_id}/{supplier_id}", summary="修改投标记录字段", description="修改投标记录的部分字段")
async def update_bid_record(
    project_id: int,
    supplier_id: int,
    update_data: BidRecordUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    修改投标记录字段
    
    - **project_id**: 项目ID
    - **supplier_id**: 供应商ID
    - **update_data**: 要更新的字段（可选字段，只更新提供的字段）
        - bid_document_file_id: 投标文件ID
        - ai_preliminary_review: AI初审（JSON）
        - ai_preliminary_review_model_session: AI初审_model_session
        - ai_preliminary_review_success: AI初审成功
        - preliminary_review: 人工初审（JSON）
        - ai_evaluation: AI评审（JSON）
        - ai_evaluation_success: AI评审成功
    
    返回更新后的投标记录信息
    """
    # 查询投标记录是否存在
    bid_record = db.query(BidRecord).filter(
        BidRecord.project_id == project_id,
        BidRecord.supplier_id == supplier_id
    ).first()
    if not bid_record:
        raise HTTPException(
            status_code=404,
            detail=f"投标记录（项目 ID {project_id}，供应商 ID {supplier_id}）不存在"
        )
    
    try:
        # 更新提供的字段
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # 如果更新了 bid_document_file_id，验证文件是否存在
        if "bid_document_file_id" in update_dict and update_dict["bid_document_file_id"]:
            file_record = db.query(File).filter(
                File.file_id == update_dict["bid_document_file_id"]
            ).first()
            if not file_record:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件 ID {update_dict['bid_document_file_id']} 不存在"
                )
        
        # 更新字段
        for field, value in update_dict.items():
            setattr(bid_record, field, value)
        
        # 提交事务
        db.commit()
        db.refresh(bid_record)
        
        # 查询关联的项目和供应商信息
        project = db.query(Project).filter(Project.id == project_id).first()
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        
        # 构建返回结果
        result = {
            "project_id": bid_record.project_id,
            "supplier_id": bid_record.supplier_id,
            "bid_document_file_id": bid_record.bid_document_file_id,
            "ai_preliminary_review": bid_record.ai_preliminary_review,
            "ai_preliminary_review_model_session": bid_record.ai_preliminary_review_model_session,
            "ai_preliminary_review_success": bid_record.ai_preliminary_review_success,
            "preliminary_review": bid_record.preliminary_review,
            "ai_evaluation": bid_record.ai_evaluation,
            "ai_evaluation_success": bid_record.ai_evaluation_success,
            "submission_time": bid_record.submission_time.isoformat() if bid_record.submission_time else None,
            "project": {
                "id": project.id,
                "name": project.name
            } if project else None,
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "registration_number": supplier.registration_number
            } if supplier else None
        }
        
        return result
    
    except HTTPException:
        db.rollback()
        raise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改投标记录失败: {str(e)}")