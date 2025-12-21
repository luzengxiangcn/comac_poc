"""
配置文件
"""
import os
from pathlib import Path
from typing import Optional


class Settings:
    """应用配置类"""
    
    # LLM API 配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "sk-pmssdirguurrhtfuxnvwthumkhgbenwfkfkkizhgvkwycuba")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    
    # 数据文件夹配置
    # 默认地址 项目根目录下的data文件夹
    data_folder: str = os.getenv("DATA_FOLDER", str(Path(__file__).parent.parent.parent / "data"))


# 创建全局配置实例
settings = Settings()

