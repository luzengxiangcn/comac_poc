"""
数据库配置和会话管理
"""
import sqlite3
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .data_models import Base

# 数据库URL配置（默认使用SQLite，可根据需要修改）
DATABASE_URL = "sqlite:///./comac_purchase.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if "sqlite" in DATABASE_URL
        else {}
    ),
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=False  # 设置为 True 可以查看 SQL 语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _check_and_migrate_bid_records():
    """检查并迁移 bid_records 表结构（如果需要）"""
    if "sqlite" not in DATABASE_URL:
        return  # 只处理 SQLite 数据库
    
    # 获取数据库文件路径
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not Path(db_path).exists():
        return  # 数据库文件不存在，create_all 会创建
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bid_records'")
        if not cursor.fetchone():
            return  # 表不存在，create_all 会创建
        
        # 检查是否已经迁移过（检查是否有 id 列）
        cursor.execute("PRAGMA table_info(bid_records)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'id' in columns:
            return  # 已经迁移过
        
        print("检测到 bid_records 表需要迁移，开始迁移...")
        
        # 执行迁移
        cursor.execute("""
            CREATE TABLE bid_records_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                supplier_id INTEGER,
                bid_document_file_id VARCHAR(36),
                identity_recognition_model_session TEXT,
                ai_preliminary_review JSON,
                ai_preliminary_review_model_session TEXT,
                ai_preliminary_review_success BOOLEAN DEFAULT 0,
                preliminary_review JSON,
                ai_evaluation JSON,
                ai_evaluation_success BOOLEAN DEFAULT 0,
                submission_time DATETIME,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (bid_document_file_id) REFERENCES files(file_id),
                UNIQUE(project_id, bid_document_file_id)
            )
        """)
        
        cursor.execute("""
            INSERT INTO bid_records_new (
                project_id,
                supplier_id,
                bid_document_file_id,
                identity_recognition_model_session,
                ai_preliminary_review,
                ai_preliminary_review_model_session,
                ai_preliminary_review_success,
                preliminary_review,
                ai_evaluation,
                ai_evaluation_success,
                submission_time
            )
            SELECT 
                project_id,
                supplier_id,
                bid_document_file_id,
                NULL as identity_recognition_model_session,
                ai_preliminary_review,
                ai_preliminary_review_model_session,
                ai_preliminary_review_success,
                preliminary_review,
                ai_evaluation,
                ai_evaluation_success,
                submission_time
            FROM bid_records
        """)
        
        cursor.execute("DROP TABLE bid_records")
        cursor.execute("ALTER TABLE bid_records_new RENAME TO bid_records")
        
        # 创建索引
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bid_records_project_id ON bid_records(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bid_records_supplier_id ON bid_records(supplier_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bid_records_file_id ON bid_records(bid_document_file_id)")
        except Exception:
            pass
        
        conn.commit()
        print("bid_records 表迁移完成")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移 bid_records 表时出错: {e}")
    finally:
        conn.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 先检查并迁移 bid_records 表（如果需要）
    _check_and_migrate_bid_records()
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    使用示例：
        db = next(get_db())
        # 使用 db 进行数据库操作
        db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
