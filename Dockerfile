# 多阶段构建 Dockerfile
# 阶段1: 前端构建
FROM node:18-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app/front

# 设置 npm 使用淘宝镜像
RUN npm config set registry https://registry.npmmirror.com

# 复制前端依赖文件
COPY front/package.json front/package-lock.json* ./

# 安装前端依赖（包括 devDependencies，构建需要）
RUN npm ci || npm install

# 复制前端源代码
COPY front/ ./

# 构建前端
RUN npm run build

# 阶段2: 后端运行环境
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 替换 apt 源为阿里云镜像
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list || \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main" >> /etc/apt/sources.list

# 安装系统依赖（如果需要）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖文件
COPY requirements.txt ./

# 安装 Python 依赖（使用清华镜像）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 从构建阶段复制前端构建产物
COPY --from=frontend-builder /app/front/dist ./front/dist

# 复制后端源代码
COPY src/ ./src/
COPY __init__.py ./

# 设置 Python 路径
ENV PYTHONPATH=/app/src

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "comac_purchase.app:app", "--host", "0.0.0.0", "--port", "8000"]

