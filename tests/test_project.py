"""
测试项目相关的 API 接口
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

# 必须在导入其他模块之前设置路径（使用绝对路径）
_test_file = Path(__file__).resolve()
_project_root = _test_file.parent.parent.resolve()
_src_path = _project_root / "src"
_src_path_str = str(_src_path)
# 确保路径在 sys.path 的最前面
if _src_path_str in sys.path:
    sys.path.remove(_src_path_str)
sys.path.insert(0, _src_path_str)

# 调试：验证路径和导入
if __name__ != "__main__":
    # 只在 pytest 运行时打印
    import os
    if os.environ.get("PYTEST_CURRENT_TEST"):
        print(f"DEBUG: sys.path[0] = {sys.path[0]}")
        print(f"DEBUG: _src_path_str = {_src_path_str}")
        print(f"DEBUG: Path exists: {_src_path.exists()}")
        try:
            import comac_purchase
            print(f"DEBUG: comac_purchase imported: {comac_purchase.__file__}")
        except Exception as e:
            print(f"DEBUG: Failed to import comac_purchase: {e}")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# 正常导入（路径已在 conftest.py 和上面设置）
from comac_purchase.app.router.project import router
from comac_purchase.db.data_models import Base, File, Project


# 创建测试数据库
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_test_db() -> Generator[Session, None, None]:
    """测试数据库会话"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库表"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def temp_data_folder():
    """创建临时数据文件夹"""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_data_folder = os.environ.get("DATA_FOLDER")
        os.environ["DATA_FOLDER"] = tmpdir
        yield Path(tmpdir)
        if original_data_folder:
            os.environ["DATA_FOLDER"] = original_data_folder
        elif "DATA_FOLDER" in os.environ:
            del os.environ["DATA_FOLDER"]


@pytest.fixture(scope="function")
def app(test_db, temp_data_folder):
    """创建 FastAPI 应用实例"""
    from comac_purchase.db import get_db
    
    app = FastAPI()
    app.include_router(router)
    
    # 覆盖 get_db 依赖
    app.dependency_overrides[get_db] = get_test_db
    
    yield app
    
    # 清除依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app):
    """创建测试客户端"""
    return TestClient(app)


def test_create_project_success(client, temp_data_folder):
    """测试成功创建项目"""
    # 准备测试数据 - 使用 Word 文档格式
    project_name = "测试项目"
    # 创建一个简单的 docx 文件内容（ZIP 格式的头部）
    file_content = b"PK\x03\x04" + b"test content"  # 模拟 docx 文件（docx 是 ZIP 格式）
    file_name = "test_tender.docx"
    
    # 发送请求
    response = client.post(
        "/project/",
        data={"name": project_name},
        files={"file": (file_name, file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == project_name
    assert data["id"] is not None
    assert data["tender_document_file_id"] is not None
    assert data["file"]["origin_name"] == file_name
    assert data["file"]["file_id"] == data["tender_document_file_id"]
    
    # 验证文件已保存
    files_folder = temp_data_folder / "files"
    assert files_folder.exists()
    saved_file = list(files_folder.glob("*"))
    assert len(saved_file) == 1
    assert saved_file[0].read_bytes() == file_content


def test_create_project_without_file(client):
    """测试未上传文件时创建项目失败"""
    response = client.post(
        "/project/",
        data={"name": "测试项目"},
        files={"file": ("", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}  # 空文件名
    )
    
    assert response.status_code == 400
    assert "必须上传招标文件" in response.json()["detail"]


def test_create_project_invalid_file_type(client):
    """测试上传非 Word 文档时失败"""
    file_content = b"test content"
    file_name = "test.pdf"
    
    response = client.post(
        "/project/",
        data={"name": "测试项目"},
        files={"file": (file_name, file_content, "application/pdf")}
    )
    
    assert response.status_code == 400
    assert "必须是 Word 文档格式" in response.json()["detail"]


def test_create_project_database_records(client, temp_data_folder):
    """测试数据库记录是否正确创建"""
    project_name = "数据库测试项目"
    file_content = b"PK\x03\x04" + b"test content"
    file_name = "test.docx"
    
    # 创建项目
    response = client.post(
        "/project/",
        data={"name": project_name},
        files={"file": (file_name, file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    
    assert response.status_code == 200
    data = response.json()
    project_id = data["id"]
    file_id = data["tender_document_file_id"]
    
    # 验证数据库记录
    db = next(get_test_db())
    try:
        # 验证项目记录
        project = db.query(Project).filter(Project.id == project_id).first()
        assert project is not None
        assert project.name == project_name
        assert project.tender_document_file_id == file_id
        
        # 验证文件记录
        file_record = db.query(File).filter(File.file_id == file_id).first()
        assert file_record is not None
        assert file_record.origin_name == file_name
        assert file_record.file_name is not None
        
        # 验证关联关系
        assert project.tender_file.file_id == file_id
    finally:
        db.close()


def test_create_project_multiple_files(client, temp_data_folder):
    """测试创建多个项目"""
    # 创建第一个项目
    response1 = client.post(
        "/project/",
        data={"name": "项目1"},
        files={"file": ("file1.docx", b"PK\x03\x04content1", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response1.status_code == 200
    
    # 创建第二个项目
    response2 = client.post(
        "/project/",
        data={"name": "项目2"},
        files={"file": ("file2.doc", b"content2", "application/msword")}
    )
    assert response2.status_code == 200
    
    # 验证两个项目都创建成功
    data1 = response1.json()
    data2 = response2.json()
    assert data1["id"] != data2["id"]
    assert data1["name"] == "项目1"
    assert data2["name"] == "项目2"
    
    # 验证文件都已保存
    files_folder = temp_data_folder / "files"
    saved_files = list(files_folder.glob("*"))
    assert len(saved_files) == 2


def test_create_project_file_content_preserved(client, temp_data_folder):
    """测试文件内容是否正确保存"""
    file_content = b"PK\x03\x04" + b"test document content\nTest content with English"
    file_name = "test_document.docx"
    
    response = client.post(
        "/project/",
        data={"name": "文件内容测试"},
        files={"file": (file_name, file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证文件内容
    files_folder = temp_data_folder / "files"
    file_name_uuid = data["file"]["file_name"]
    saved_file_path = files_folder / file_name_uuid
    assert saved_file_path.exists()
    assert saved_file_path.read_bytes() == file_content


def test_create_project_with_doc_format(client, temp_data_folder):
    """测试上传 .doc 格式文件"""
    file_content = b"test doc content"
    file_name = "test.doc"
    
    response = client.post(
        "/project/",
        data={"name": "DOC格式测试"},
        files={"file": (file_name, file_content, "application/msword")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["file"]["origin_name"] == file_name

