"""
项目相关的 API 路由
"""
import uuid
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from comac_purchase.config import settings
from comac_purchase.db import BidRecord, File as FileModel, Project, get_db

router = APIRouter(prefix="/project", tags=["project"])


async def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    """
    保存上传的文件
    
    Returns:
        tuple: (file_id, file_name)
    """
    # 验证文件类型必须是 Word 文档
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.doc', '.docx']:
        raise HTTPException(
            status_code=400,
            detail=f"文件必须是 Word 文档格式（.doc 或 .docx），当前文件格式：{file_ext}"
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
    
    return file_id, file_name


class ProjectUpdateRequest(BaseModel):
    """项目更新请求模型"""
    name: Optional[str] = None
    tender_document_file_id: Optional[str] = None
    business_requirement_file_id: Optional[str] = None
    procurement_requirement_file_id: Optional[str] = None
    ai_review_session: Optional[str] = None


@router.post("/", summary="创建项目", description="创建新项目，项目名称和各类文档为可选")
async def create_project(
    name: Annotated[Optional[str], Form(description="项目名称")] = None,
    file: Annotated[Optional[UploadFile], File(description="采购征询文件")] = None,
    business_requirement_file: Annotated[Optional[UploadFile], File(description="需求文档")] = None,
    procurement_requirement_file: Annotated[Optional[UploadFile], File(description="采购部门规范文档")] = None,
    db: Session = Depends(get_db)
):
    """
    创建新项目
    
    - **name**: 项目名称（可选，默认为"未命名"）
    - **file**: 采购征询文件（可选，必须是 Word 文档 .doc 或 .docx）
    - **business_requirement_file**: 需求文档（可选，必须是 Word 文档 .doc 或 .docx）
    - **procurement_requirement_file**: 采购部门规范文档（可选，必须是 Word 文档 .doc 或 .docx）
    
    返回创建的项目信息
    """
    try:
        tender_file_id = None
        business_requirement_file_id = None
        procurement_requirement_file_id = None
        
        # 处理采购征询文件
        if file and file.filename:
            file_id, file_name = await save_uploaded_file(file)
            tender_file_id = file_id
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=file.filename,
                file_name=file_name
            )
            db.add(file_record)
        
        # 处理需求文档
        if business_requirement_file and business_requirement_file.filename:
            file_id, file_name = await save_uploaded_file(business_requirement_file)
            business_requirement_file_id = file_id
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=business_requirement_file.filename,
                file_name=file_name
            )
            db.add(file_record)
        
        # 处理采购部门规范文档
        if procurement_requirement_file and procurement_requirement_file.filename:
            file_id, file_name = await save_uploaded_file(procurement_requirement_file)
            procurement_requirement_file_id = file_id
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=procurement_requirement_file.filename,
                file_name=file_name
            )
            db.add(file_record)
        
        # 创建项目记录
        project_name = name.strip() if name and name.strip() else "未命名"
        project = Project(
            name=project_name,
            tender_document_file_id=tender_file_id,
            business_requirement_file_id=business_requirement_file_id,
            procurement_requirement_file_id=procurement_requirement_file_id
        )
        db.add(project)
        
        # 提交事务
        db.commit()
        db.refresh(project)
        
        result = {
            "id": project.id,
            "name": project.name,
            "tender_document_file_id": project.tender_document_file_id,
            "business_requirement_file_id": project.business_requirement_file_id,
            "procurement_requirement_file_id": project.procurement_requirement_file_id
        }
        
        return result
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/", summary="获取项目列表", description="获取所有项目列表，包含供应商数量")
async def get_projects(db: Session = Depends(get_db)):
    """
    获取所有项目列表
    
    返回项目列表，每个项目包含：
    - id: 项目ID
    - name: 项目名称
    - supplier_count: 供应商数量（投标记录数量）
    """
    try:
        # 查询所有项目，并统计每个项目的投标记录数量
        projects = db.query(
            Project.id,
            Project.name,
            func.count(BidRecord.project_id).label('supplier_count')
        ).outerjoin(
            BidRecord, Project.id == BidRecord.project_id
        ).group_by(
            Project.id,
            Project.name
        ).all()
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "supplier_count": p.supplier_count
            }
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/file/{file_id}/content", summary="获取文件内容", description="根据文件ID获取文件的Markdown格式内容")
async def get_file_content(file_id: str, db: Session = Depends(get_db)):
    """
    获取文件内容（Markdown格式）
    
    - **file_id**: 文件ID
    
    返回文件的Markdown格式内容
    """
    # 查询文件记录
    file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail=f"文件 ID {file_id} 不存在")
    
    # 读取文件内容并转换为Markdown
    try:
        markdown_content = file_record.read_content_as_mark_down(settings.data_folder)
        if markdown_content is None:
            raise HTTPException(status_code=500, detail="无法读取文件内容")
        
        return {
            "content": markdown_content,
            "file_id": file_record.file_id,
            "origin_name": file_record.origin_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.get("/file/{file_id}/download", summary="下载文件", description="根据文件ID下载原始文件")
async def download_file(file_id: str, db: Session = Depends(get_db)):
    """
    下载文件
    
    - **file_id**: 文件ID
    
    返回原始文件（docx格式）
    """
    # 查询文件记录
    file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail=f"文件 ID {file_id} 不存在")
    
    # 构建文件路径
    files_folder = Path(settings.data_folder) / "files"
    file_path = files_folder / file_record.file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回文件
    return FileResponse(
        path=str(file_path),
        filename=file_record.origin_name,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@router.get("/{project_id}", summary="获取项目详情", description="根据项目ID获取项目详情")
async def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """
    获取项目详情
    
    - **project_id**: 项目ID
    
    返回项目详情信息
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    # 统计供应商数量
    supplier_count = db.query(func.count(BidRecord.project_id)).filter(
        BidRecord.project_id == project_id
    ).scalar()
    
    return {
        "id": project.id,
        "name": project.name,
        "business_requirement_file_id": project.business_requirement_file_id,
        "procurement_requirement_file_id": project.procurement_requirement_file_id,
        "tender_document_file_id": project.tender_document_file_id,
        "supplier_count": supplier_count
    }


@router.get("/{project_id}/tender-document", summary="获取项目采购征询文件内容", description="获取项目采购征询文件的Markdown格式内容")
async def get_project_tender_document(project_id: int, db: Session = Depends(get_db)):
    """
    获取项目采购征询文件内容（Markdown格式）
    
    - **project_id**: 项目ID
    
    返回采购征询文件的Markdown格式内容
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    if not project.tender_document_file_id:
        raise HTTPException(status_code=404, detail="该项目没有采购征询文件")
    
    # 查询文件记录
    file_record = db.query(FileModel).filter(FileModel.file_id == project.tender_document_file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="采购征询文件不存在")
    
    # 读取文件内容并转换为Markdown
    try:
        markdown_content = file_record.read_content_as_mark_down(settings.data_folder)
        if markdown_content is None:
            raise HTTPException(status_code=500, detail="无法读取采购征询文件内容")
        
        return {
            "content": markdown_content,
            "file_id": file_record.file_id,
            "origin_name": file_record.origin_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取采购征询文件失败: {str(e)}")


@router.post("/{project_id}/upload-documents", summary="上传项目文档", description="上传需求文档、采购部门规范文档或采购征询文件")
async def upload_project_documents(
    project_id: int,
    business_requirement_file: Annotated[Optional[UploadFile], File(description="需求文档")] = None,
    procurement_requirement_file: Annotated[Optional[UploadFile], File(description="采购部门规范文档")] = None,
    tender_document_file: Annotated[Optional[UploadFile], File(description="采购征询文件")] = None,
    db: Session = Depends(get_db)
):
    """
    上传项目文档
    
    - **project_id**: 项目ID
    - **business_requirement_file**: 需求文档（可选，必须是 Word 文档 .doc 或 .docx）
    - **procurement_requirement_file**: 采购部门规范文档（可选，必须是 Word 文档 .doc 或 .docx）
    - **tender_document_file**: 采购征询文件（可选，必须是 Word 文档 .doc 或 .docx）
    
    返回更新后的项目信息
    """
    # 查询项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    try:
        # 处理需求文档
        if business_requirement_file and business_requirement_file.filename:
            file_id, file_name = await save_uploaded_file(business_requirement_file)
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=business_requirement_file.filename,
                file_name=file_name
            )
            db.add(file_record)
            project.business_requirement_file_id = file_id
        
        # 处理采购部门规范文档
        if procurement_requirement_file and procurement_requirement_file.filename:
            file_id, file_name = await save_uploaded_file(procurement_requirement_file)
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=procurement_requirement_file.filename,
                file_name=file_name
            )
            db.add(file_record)
            project.procurement_requirement_file_id = file_id
        
        # 处理采购征询文件
        if tender_document_file and tender_document_file.filename:
            file_id, file_name = await save_uploaded_file(tender_document_file)
            
            # 创建文件记录
            file_record = FileModel(
                file_id=file_id,
                origin_name=tender_document_file.filename,
                file_name=file_name
            )
            db.add(file_record)
            project.tender_document_file_id = file_id
        
        # 提交事务
        db.commit()
        db.refresh(project)
        
        # 统计供应商数量
        supplier_count = db.query(func.count(BidRecord.project_id)).filter(
            BidRecord.project_id == project_id
        ).scalar()
        
        return {
            "id": project.id,
            "name": project.name,
            "business_requirement_file_id": project.business_requirement_file_id,
            "procurement_requirement_file_id": project.procurement_requirement_file_id,
            "tender_document_file_id": project.tender_document_file_id,
            "supplier_count": supplier_count
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传文档失败: {str(e)}")


@router.delete("/{project_id}", summary="删除项目", description="根据项目ID删除项目及其相关数据")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    删除项目
    
    - **project_id**: 项目ID
    
    删除项目及其相关的投标记录和生成记录
    """
    # 查询项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    try:
        # 删除项目（由于cascade关系，相关的BidRecord和TenderGeneration会自动删除）
        db.delete(project)
        db.commit()
        
        return {"message": "项目删除成功"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


@router.patch("/{project_id}", summary="修改项目字段", description="修改项目的部分字段")
async def update_project(
    project_id: int,
    update_data: ProjectUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    修改项目字段
    
    - **project_id**: 项目ID
    - **update_data**: 要更新的字段（可选字段，只更新提供的字段）
        - name: 项目名称
        - tender_document_file_id: 采购征询文件ID
        - ai_review_session: AI评审 session
    
    返回更新后的项目信息
    """
    # 查询项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    try:
        # 更新提供的字段
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # 验证文件ID是否存在
        file_id_fields = ["tender_document_file_id", "business_requirement_file_id", "procurement_requirement_file_id"]
        for field in file_id_fields:
            if field in update_dict and update_dict[field]:
                file_record = db.query(FileModel).filter(
                    FileModel.file_id == update_dict[field]
                ).first()
                if not file_record:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件 ID {update_dict[field]} 不存在"
                    )
        
        # 更新字段
        for field, value in update_dict.items():
            setattr(project, field, value)
        
        # 提交事务
        db.commit()
        db.refresh(project)
        
        # 统计供应商数量
        supplier_count = db.query(func.count(BidRecord.project_id)).filter(
            BidRecord.project_id == project_id
        ).scalar()
        
        return {
            "id": project.id,
            "name": project.name,
            "tender_document_file_id": project.tender_document_file_id,
            "business_requirement_file_id": project.business_requirement_file_id,
            "procurement_requirement_file_id": project.procurement_requirement_file_id,
            "ai_review_session": project.ai_review_session,
            "supplier_count": supplier_count
        }
    
    except HTTPException:
        db.rollback()
        raise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改项目失败: {str(e)}")

