"""
pytest 配置文件
"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径（必须在最前面执行，使用绝对路径）
_project_root = Path(__file__).parent.parent.resolve()
_src_path = _project_root / "src"
_src_path_str = str(_src_path)
if _src_path_str not in sys.path:
    sys.path.insert(0, _src_path_str)


def pytest_configure(config):
    """pytest 配置钩子，确保路径已设置"""
    # 再次确保路径已设置
    _project_root = Path(__file__).parent.parent.resolve()
    _src_path = _project_root / "src"
    _src_path_str = str(_src_path)
    if _src_path_str not in sys.path:
        sys.path.insert(0, _src_path_str)

