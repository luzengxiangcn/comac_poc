# COMAC Purchase

## 项目简介

这是一个 Python 项目，用于处理采购相关业务。

## 项目结构

```
comac_purchase/
├── src/
│   └── comac_purchase/
│       ├── __init__.py
│       ├── main.py
│       ├── db/                    # 数据库模块
│       │   ├── __init__.py
│       │   ├── models.py          # SQLAlchemy 数据模型
│       │   └── database.py        # 数据库配置和会话管理
│       └── examples/              # 示例代码
│           ├── __init__.py
│           └── example.py         # 数据模型使用示例
├── tests/                         # 测试目录
├── requirements.txt               # Python 依赖
├── .gitignore                    # Git 忽略文件
└── README.md                     # 项目说明文档
```

## 环境要求

- Python 3.8+

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 初始化数据库

```python
from comac_purchase import init_db

# 创建数据库表
init_db()
```

### 使用数据模型

```python
from comac_purchase import Project, Supplier, BidRecord, SessionLocal

# 创建数据库会话
db = SessionLocal()

# 创建项目
project = Project(name="项目名称", tender_document="招标书内容")
db.add(project)
db.commit()
```

### 运行示例

```bash
python -m src.comac_purchase.examples.example
```

## 开发

### 运行测试

```bash
pytest
```

## 许可证

[在此添加许可证信息]

