"""
迁移 bid_records 表结构
将主键从联合主键 (project_id, supplier_id) 改为自增 id
"""
import sqlite3
from pathlib import Path

# 数据库文件路径（根据实际情况修改）
DB_PATH = Path("./comac_purchase.db")

def migrate_bid_records():
    """迁移 bid_records 表结构"""
    if not DB_PATH.exists():
        print(f"数据库文件不存在: {DB_PATH}")
        print("如果是新数据库，直接运行应用即可自动创建表结构")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bid_records'")
        if not cursor.fetchone():
            print("bid_records 表不存在，无需迁移")
            return
        
        # 检查是否已经迁移过（检查是否有 id 列）
        cursor.execute("PRAGMA table_info(bid_records)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'id' in columns:
            print("表结构已经迁移过，无需重复迁移")
            return
        
        print("开始迁移 bid_records 表...")
        
        # 1. 创建新表结构
        print("创建新表结构...")
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
        
        # 2. 复制数据（如果没有 id 列，需要生成临时 id）
        print("复制数据...")
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
        
        # 3. 删除旧表
        print("删除旧表...")
        cursor.execute("DROP TABLE bid_records")
        
        # 4. 重命名新表
        print("重命名新表...")
        cursor.execute("ALTER TABLE bid_records_new RENAME TO bid_records")
        
        # 5. 创建索引（如果需要）
        print("创建索引...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bid_records_project_id ON bid_records(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bid_records_supplier_id ON bid_records(supplier_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bid_records_file_id ON bid_records(bid_document_file_id)")
        except Exception as e:
            print(f"创建索引时出现警告（可能已存在）: {e}")
        
        # 提交事务
        conn.commit()
        print("迁移完成！")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(bid_records)")
        columns = cursor.fetchall()
        print("\n新表结构：")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        cursor.execute("SELECT COUNT(*) FROM bid_records")
        count = cursor.fetchone()[0]
        print(f"\n数据记录数: {count}")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_bid_records()

