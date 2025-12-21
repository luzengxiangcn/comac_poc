"""
SQLAlchemy 数据模型
"""
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime

Base = declarative_base()


class File(Base):
    """文件模型 - 用来上传或下载文件"""
    __tablename__ = 'files'

    file_id = Column(String(36), primary_key=True, comment='文件ID（UUID）')
    origin_name = Column(String(255), nullable=False, comment='上传文件的名称')
    file_name = Column(String(36), nullable=False, comment='保存文件的uuid')

    # 关系
    projects_tender_file = relationship('Project', back_populates='tender_file', foreign_keys='Project.tender_document_file_id')
    projects_business_requirement = relationship('Project', foreign_keys='Project.business_requirement_file_id')
    projects_procurement_requirement = relationship('Project', foreign_keys='Project.procurement_requirement_file_id')
    bid_records = relationship('BidRecord', back_populates='bid_file')
    tender_generations_file = relationship('TenderGeneration', foreign_keys='TenderGeneration.file_id')
    tender_generations_business_requirement = relationship('TenderGeneration', foreign_keys='TenderGeneration.business_requirement_file_id')
    tender_generations_procurement_requirement = relationship('TenderGeneration', foreign_keys='TenderGeneration.procurement_requirement_file_id')

    def __repr__(self):
        return f"<File(file_id='{self.file_id}', origin_name='{self.origin_name}')>"
    
    def _is_word_file(self) -> bool:
        """判断是否是 Word 文件"""
        if not self.origin_name:
            return False
        ext = Path(self.origin_name).suffix.lower()
        return ext in ['.doc', '.docx']
    
    def read_content_as_mark_down(self, data_folder: str) -> Optional[str]:
        """
        读取文件内容并转换为 Markdown 格式
        
        Args:
            data_folder: 数据文件夹路径
            
        Returns:
            Markdown 格式的字符串，如果不是 Word 文件或读取失败则返回 None
        """
        if not self._is_word_file():
            return None
        
        try:
            # 构建文件路径
            files_folder = Path(data_folder) / "files"
            file_path = files_folder / self.file_name
            
            if not file_path.exists():
                return None
            
            # 判断文件类型
            ext = Path(self.origin_name).suffix.lower()
            
            if ext == '.docx':
                return self._docx_to_markdown(file_path)
            elif ext == '.doc':
                # .doc 格式较老，需要特殊处理
                # 这里可以提示不支持或使用其他库
                return self._doc_to_markdown(file_path)
            
            return None
        except Exception as e:
            # 静默处理错误，返回 None
            return None
    
    def _docx_to_markdown(self, file_path: Path) -> str:
        """将 .docx 文件转换为 Markdown"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            markdown_lines = []
            
            # 遍历文档中的所有元素，保持顺序
            # 使用 python-docx 的 element.body 来保持段落和表格的顺序
            for element in doc.element.body:
                # 处理段落
                if element.tag.endswith('p'):
                    from docx.oxml.text.paragraph import CT_P
                    from docx.text.paragraph import Paragraph
                    
                    if isinstance(element, CT_P):
                        para = Paragraph(element, doc)
                        text = para.text.strip()
                        if text:
                            # 检查是否是标题
                            if para.style and ('Heading' in para.style.name or '标题' in para.style.name):
                                level = self._get_heading_level(para.style.name)
                                if level > 0:
                                    markdown_lines.append('#' * level + ' ' + text)
                                else:
                                    markdown_lines.append(text)
                            else:
                                markdown_lines.append(text)
                
                # 处理表格
                elif element.tag.endswith('tbl'):
                    from docx.oxml.table import CT_Tbl
                    from docx.table import Table
                    
                    if isinstance(element, CT_Tbl):
                        table = Table(element, doc)
                        markdown_table = self._table_to_markdown(table)
                        if markdown_table:
                            markdown_lines.append('')
                            markdown_lines.append(markdown_table)
                            markdown_lines.append('')
            
            return '\n'.join(markdown_lines)
        except ImportError:
            raise ImportError("需要安装 python-docx 库: pip install python-docx")
        except Exception as e:
            raise Exception(f"解析 Word 文件失败: {str(e)}")
    
    def _doc_to_markdown(self, file_path: Path) -> str:
        """将 .doc 文件转换为 Markdown（需要额外处理）"""
        # .doc 格式较老，python-docx 不支持
        # 提示用户转换为 .docx 格式
        raise NotImplementedError(
            "不支持 .doc 格式，请将文件转换为 .docx 格式。"
            "可以使用 Microsoft Word 或其他工具进行转换。"
        )
    
    def _get_heading_level(self, style_name: str) -> int:
        """从样式名称获取标题级别"""
        if 'Heading 1' in style_name or '标题 1' in style_name:
            return 1
        elif 'Heading 2' in style_name or '标题 2' in style_name:
            return 2
        elif 'Heading 3' in style_name or '标题 3' in style_name:
            return 3
        elif 'Heading 4' in style_name or '标题 4' in style_name:
            return 4
        elif 'Heading 5' in style_name or '标题 5' in style_name:
            return 5
        elif 'Heading 6' in style_name or '标题 6' in style_name:
            return 6
        return 0
    
    def _table_to_markdown(self, table) -> str:
        """将表格转换为 Markdown 格式，保留表格信息"""
        markdown_lines = []
        
        # 获取表格数据
        rows_data = []
        for row in table.rows:
            row_data = []
            for cell in row.cells:
                # 获取单元格文本，替换换行符为空格，转义管道符
                cell_text = cell.text.strip().replace('\n', ' ').replace('|', '\\|')
                row_data.append(cell_text)
            rows_data.append(row_data)
        
        if not rows_data:
            return ''
        
        # 确定列数
        max_cols = max(len(row) for row in rows_data) if rows_data else 0
        if max_cols == 0:
            return ''
        
        # 确保所有行的列数一致
        for row in rows_data:
            while len(row) < max_cols:
                row.append('')
        
        # 生成表头（第一行）
        header = rows_data[0] if rows_data else []
        markdown_lines.append('| ' + ' | '.join(header) + ' |')
        
        # 生成分隔行
        markdown_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
        
        # 生成数据行
        for row in rows_data[1:]:
            markdown_lines.append('| ' + ' | '.join(row) + ' |')
        
        return '\n'.join(markdown_lines)


class Project(Base):
    """项目模型 - 采购项目"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, comment='项目ID')
    name = Column(String(255), nullable=False, default='未命名', comment='项目名称（默认：未命名）')
    business_requirement_file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='业务需求文件ID（外键）')
    procurement_requirement_file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='采购部门要求ID（外键）')
    tender_document_file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='采购征询文件ID（外键）')
    ai_review_session = Column(Text, comment='AI评审 session')

    # 关系
    bid_records = relationship('BidRecord', back_populates='project', cascade='all, delete-orphan')
    tender_file = relationship('File', back_populates='projects_tender_file', foreign_keys=[tender_document_file_id])
    business_requirement_file = relationship('File', foreign_keys=[business_requirement_file_id], overlaps="projects_business_requirement")
    procurement_requirement_file = relationship('File', foreign_keys=[procurement_requirement_file_id], overlaps="projects_procurement_requirement")
    tender_generations = relationship('TenderGeneration', back_populates='project', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class TenderGeneration(Base):
    """生成采购征询文件模型"""
    __tablename__ = 'tender_generations'

    id = Column(Integer, primary_key=True, comment='生成采购征询文件ID')
    business_requirement_file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='业务需求文件ID（外键）')
    procurement_requirement_file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='采购部门要求ID（外键）')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID（外键，非空）')
    file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='生成的文件ID（外键，可为空）')
    model_session = Column(Text, comment='model_session')
    status = Column(String(20), nullable=False, default='running', comment='状态：running, finished, failed')

    # 关系
    project = relationship('Project', back_populates='tender_generations')
    business_requirement_file = relationship('File', foreign_keys=[business_requirement_file_id], overlaps="tender_generations_business_requirement")
    procurement_requirement_file = relationship('File', foreign_keys=[procurement_requirement_file_id], overlaps="tender_generations_procurement_requirement")
    generated_file = relationship('File', foreign_keys=[file_id], overlaps="tender_generations_file")

    def __repr__(self):
        return f"<TenderGeneration(id={self.id}, project_id={self.project_id}, status='{self.status}')>"


class Supplier(Base):
    """供应商模型"""
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True, comment='供应商ID')
    name = Column(String(255), nullable=False, comment='供应商名称')
    registration_number = Column(String(100), unique=True, nullable=False, comment='社会信用代码')

    # 关系
    bid_records = relationship('BidRecord', back_populates='supplier', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', registration_number='{self.registration_number}')>"


class BidRecord(Base):
    """投标记录模型 - 记录每个项目、供应商的投标情况"""
    __tablename__ = 'bid_records'

    id = Column(Integer, primary_key=True, comment='投标记录ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID（外键）')
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True, comment='供应商ID（外键，可为空）')
    bid_document_file_id = Column(String(36), ForeignKey('files.file_id'), nullable=True, comment='投标文件ID（外键，可为null）')
    identity_recognition_model_session = Column(Text, comment='身份识别_model_session')
    ai_preliminary_review = Column(JSON, comment='AI初审（JSON）')
    ai_preliminary_review_model_session = Column(Text, comment='AI初审_model_session')
    ai_preliminary_review_success = Column(Boolean, nullable=True, comment='AI初审成功：False, True, null（默认）')
    preliminary_review = Column(JSON, comment='人工初审（JSON）')
    ai_evaluation = Column(JSON, comment='AI评审（JSON）')
    ai_evaluation_success = Column(Boolean, nullable=True, comment='AI评审成功：False, True, null（默认）')
    submission_time = Column(DateTime, default=datetime.utcnow, comment='投标文件入库时间')

    # 关系
    project = relationship('Project', back_populates='bid_records')
    supplier = relationship('Supplier', back_populates='bid_records')
    bid_file = relationship('File', back_populates='bid_records', foreign_keys=[bid_document_file_id])

    # 唯一约束：同一项目的同一投标文件只能有一条记录
    __table_args__ = (
        UniqueConstraint('project_id', 'bid_document_file_id', name='uq_project_bid_file'),
    )

    def __repr__(self):
        return f"<BidRecord(project_id={self.project_id}, supplier_id={self.supplier_id})>"

