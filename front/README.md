# 商飞智能采购POC - 前端项目

Vue 3 + Vite 前端项目

## 功能特性

- 项目列表展示：主页显示所有项目，以卡片形式展示项目名称和供应商数量
- 项目详情页：
  - 标书Tab：浏览项目的招标文档（Word文档转换为Markdown显示）
  - 供应商Tab：展示项目的供应商列表，支持添加新供应商
- 添加供应商：点击+号可以添加供应商，需要填写供应商名称、社会信用代码，并可选择上传投标文件

## 技术栈

- Vue 3 (Composition API)
- Vue Router 4
- Vite
- Axios

## 项目结构

```
front/
├── src/
│   ├── api/              # API服务层
│   │   ├── index.js      # Axios配置
│   │   ├── project.js    # 项目相关API
│   │   └── bid.js        # 投标记录相关API
│   ├── assets/           # 静态资源
│   │   └── style.css     # 全局样式
│   ├── components/       # 组件
│   │   ├── ProjectCard.vue           # 项目卡片
│   │   ├── SupplierCard.vue          # 供应商卡片
│   │   ├── AddSupplierDialog.vue     # 添加供应商对话框
│   │   └── DocumentViewer.vue        # 标书查看器
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── views/            # 页面视图
│   │   ├── Home.vue                  # 主页（项目列表）
│   │   └── ProjectDetail.vue         # 项目详情页
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## 安装依赖

```bash
cd front
npm install
```

## 开发运行

```bash
npm run dev
```

开发服务器将在 http://localhost:5173 启动

## 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录

## API配置

前端通过代理访问后端API，代理配置在 `vite.config.js` 中：

- 开发环境：`/api` 请求会被代理到 `http://localhost:8000`
- 确保后端服务运行在 8000 端口

## 主要API接口

### 项目相关
- `GET /api/project/` - 获取项目列表
- `GET /api/project/{id}` - 获取项目详情
- `GET /api/project/{id}/tender-document` - 获取项目标书内容（Markdown）

### 投标记录相关
- `GET /api/bid/?project_id={id}` - 获取项目的投标记录列表（供应商列表）
- `POST /api/bid/` - 创建投标记录（添加供应商）

## 使用说明

1. 启动后端服务（确保运行在8000端口）
2. 启动前端开发服务器：`npm run dev`
3. 访问 http://localhost:5173 查看项目列表
4. 点击项目卡片进入项目详情页
5. 在项目详情页可以：
   - 查看标书内容
   - 查看供应商列表
   - 点击+号添加新供应商

