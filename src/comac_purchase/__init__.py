"""
COMAC Purchase Package
"""

__version__ = "0.1.0"

# 从 db 模块导出所有内容
from .db import (
    Base,
    Project,
    Supplier,
    BidRecord,
    init_db,
    get_db,
    SessionLocal,
    engine,
)

__all__ = [
    'Base',
    'Project',
    'Supplier',
    'BidRecord',
    'init_db',
    'get_db',
    'SessionLocal',
    'engine',
]

