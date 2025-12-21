"""
应用模块
"""
# 从父目录的 app.py 导入 app 对象
# 由于 app 既是目录又是文件，需要使用 importlib 动态导入
import importlib.util
import sys
from pathlib import Path

# 获取 app.py 文件的路径
_parent_dir = Path(__file__).parent.parent
_app_py_file = _parent_dir / "app.py"

# 动态导入 app.py 模块
if _app_py_file.exists():
    spec = importlib.util.spec_from_file_location("comac_purchase.app_py", _app_py_file)
    app_py_module = importlib.util.module_from_spec(spec)
    # 避免重复导入
    if "comac_purchase.app_py" not in sys.modules:
        spec.loader.exec_module(app_py_module)
        sys.modules["comac_purchase.app_py"] = app_py_module
    else:
        app_py_module = sys.modules["comac_purchase.app_py"]
    # 导出 app 对象
    app = app_py_module.app
else:
    raise ImportError(f"Cannot find app.py at {_app_py_file}")

__all__ = ["app"]

