"""
LLM 重命名相关的 API 路由
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from ...config import settings
from ...db import File as FileModel, Project, get_db

router = APIRouter(prefix="/llm-rename", tags=["llm-rename"])


@router.post("/rename-project-title/{project_id}", summary="重命名项目标题", description="根据项目业务需求和采购征询文件生成简短的项目名称")
async def rename_project_title(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    根据项目业务需求（如有）和采购征询文件（如有）生成一个简短的项目名称，并直接更新项目名称
    
    - **project_id**: 项目ID
    
    返回：
    - **name**: 生成并已更新的项目名称
    
    注意：此接口需要在10秒内完成，否则会超时返回错误
    """
    # 查询项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID {project_id} 不存在")
    
    # 收集文件内容
    business_requirement_content = None
    tender_document_content = None
    
    # 读取业务需求文件内容（如果有）
    if project.business_requirement_file_id:
        business_file = db.query(FileModel).filter(
            FileModel.file_id == project.business_requirement_file_id
        ).first()
        if business_file:
            try:
                business_requirement_content = business_file.read_content_as_mark_down(settings.data_folder)
            except Exception as e:
                # 如果读取失败，记录但不中断流程
                pass
    
    # 读取采购征询文件内容（如果有）
    if project.tender_document_file_id:
        tender_file = db.query(FileModel).filter(
            FileModel.file_id == project.tender_document_file_id
        ).first()
        if tender_file:
            try:
                tender_document_content = tender_file.read_content_as_mark_down(settings.data_folder)
            except Exception as e:
                # 如果读取失败，记录但不中断流程
                pass
    
    # 构建 prompt
    prompt_parts = []
    prompt_parts.append("请根据以下信息生成一个简短的项目名称（不超过20个字）。")
    prompt_parts.append("")
    prompt_parts.append("重要要求：")
    prompt_parts.append("- 直接输出项目名称，不要包含任何其他内容")
    prompt_parts.append("- 不要包含说明、解释、前缀、后缀等任何额外文字")
    prompt_parts.append("- 只输出项目名称本身")
    
    if business_requirement_content:
        prompt_parts.append("\n## 业务需求文件内容：")
        prompt_parts.append(business_requirement_content[:2000])  # 限制长度避免过长
    
    if tender_document_content:
        prompt_parts.append("\n## 采购征询文件内容：")
        prompt_parts.append(tender_document_content[:2000])  # 限制长度避免过长
    
    if not business_requirement_content and not tender_document_content:
        raise HTTPException(
            status_code=400,
            detail="项目没有业务需求文件或采购征询文件，无法生成项目名称"
        )
    
    prompt = "\n".join(prompt_parts)
    
    # 调用 LLM API，设置4秒超时
    try:
        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        
        # 使用 asyncio.wait_for 设置4秒超时
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3.2-Exp",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的采购项目命名助手，擅长根据项目文档生成简洁、准确的采购项目名称。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=50  # 限制输出长度，只需要名称
            ),
            timeout=10.0
        )
        
        # 提取生成的名称
        generated_name = response.choices[0].message.content.strip()
        
        # 清理名称，移除可能的引号或其他标记
        generated_name = generated_name.strip('"').strip("'").strip()
        
        # 如果名称为空或过长，使用默认名称
        if not generated_name or len(generated_name) > 50:
            generated_name = "未命名项目"
        
        # 直接更新数据库中的项目名称
        try:
            project.name = generated_name
            db.commit()
            db.refresh(project)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"更新项目名称失败: {str(e)}"
            )
        
        return {
            "name": generated_name
        }
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="生成项目名称超时（超过4秒），请稍后重试"
        )
    except HTTPException:
        # 重新抛出 HTTPException
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成项目名称失败: {str(e)}"
        )

