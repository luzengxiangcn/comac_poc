# LLM工具逻辑梳理

## 1. 提交任务 (`POST /llm-tool/generate-tender`)

### 流程说明
1. **接收请求参数**：
   - `project_id`: 项目ID（必需）
   - `technical_requirement_file_id`: 业务需求文件ID
   - `procurement_requirement_file_id`: 采购部门要求文件ID

2. **验证**：
   - 验证项目是否存在
   - 验证两个文件是否存在

3. **读取文件内容**：
   - 读取技术需求文件（支持 `.docx` 和 `.md` 格式）
   - 读取采购部门要求文件（支持 `.docx` 和 `.md` 格式）

4. **构建Prompt**：
   - 将两个文件内容整合到prompt中
   - 要求LLM生成完整的采购征询文件（Markdown格式）

5. **创建数据库记录**：
   - 创建 `TenderGeneration` 记录，状态为 `running`
   - 记录项目ID、两个文件ID

6. **创建并运行LLM会话**：
   - 调用 `manager.create_and_run_session()` 创建异步LLM会话
   - 会话在后台运行，不等待完成
   - 将 `session_id` 保存到 `TenderGeneration.model_session`

7. **启动后台任务**：
   - 启动 `_generate_tender_task` 后台任务（不等待完成）
   - 后台任务负责：
     - 等待会话启动（最多20分钟）
     - 等待会话完成（最多20分钟）
     - 从 `session.response_list` 提取markdown内容
     - 将markdown转换为docx文件
     - 创建 `File` 记录
     - 更新 `TenderGeneration` 记录：
       - `file_id`: 生成的docx文件ID
       - `status`: `finished`（成功）或 `failed`（失败）

8. **立即返回响应**：
   - `tender_generation_id`: 生成记录ID
   - `session_id`: LLM会话ID
   - `status`: 当前状态（`running`）
   - `message`: 提示信息

### 关键点
- 接口立即返回，不等待生成完成
- 实际生成在后台异步进行
- 通过 `tender_generation_id` 或 `session_id` 查询任务状态

---

## 2. 查询任务 (`GET /llm-tool/tender-generation/{project_id}/list`)

### 流程说明
1. **验证项目是否存在**

2. **查询生成记录**：
   - 查询该项目的所有 `TenderGeneration` 记录
   - 按ID倒序排列（最新的在前）

3. **返回结果**：
   - 每条记录包含：
     - `tender_generation_id`: 生成记录ID
     - `session_id`: 会话ID（`model_session`字段）
     - `status`: 状态（`running`, `finished`, `failed`）
     - `file_id`: 生成的文件ID（如果已完成）
     - `file_name`: 生成的文件名称（如果已完成）

### 判断成功标准
- **成功**：`status == 'finished'` 且 `file_id` 不为空
- **运行中**：`status == 'running'`
- **失败**：`status == 'failed'`

---

## 3. 流式接口 (`GET /llm-tool/tender-generation/{tender_generation_id}/stream`)

### 流程说明
1. **查询生成记录**：
   - 根据 `tender_generation_id` 查询 `TenderGeneration` 记录

2. **验证会话ID**：
   - 检查 `model_session` 字段是否存在
   - 如果不存在，返回错误

3. **获取会话**：
   - 从 `model_session_manager` 中通过 `session_id` 获取会话
   - `manager.get_session(session_id)` 会：
     - 优先从活跃会话（`LiveSession`）中获取
     - 如果不存在，从历史会话（`HistorySession`）中加载

4. **流式返回**：
   - 调用 `session.get_response()` 获取异步生成器
   - 遍历chunk，通过SSE格式返回：
     - 发送状态信息：`{'type': 'status', 'status': ...}`
     - 发送内容块：`{'type': 'chunk', 'content': ...}`
     - 发送完成状态：`{'type': 'status', 'status': 'finished'}`

### 关键点
- **直接从model_session获取session，使用get_response流式返回**
- 不需要读取docx文件，因为session中已经保存了完整的响应内容
- 支持实时流式输出（会话运行中）和历史内容流式输出（会话已完成）

---

## 数据流图

```
用户请求
  ↓
[1] POST /generate-tender
  ├─ 创建 TenderGeneration (status=running)
  ├─ 创建 LLM Session (后台运行)
  └─ 返回 tender_generation_id + session_id
      ↓
  [后台任务] _generate_tender_task
      ├─ 等待会话完成
      ├─ 提取 markdown 内容
      ├─ 转换为 docx 文件
      ├─ 创建 File 记录
      └─ 更新 TenderGeneration (file_id, status=finished)

[2] GET /tender-generation/{project_id}/list
  └─ 返回所有生成记录（包含 status 和 file_id）

[3] GET /tender-generation/{tender_generation_id}/stream
  ├─ 从 TenderGeneration 获取 model_session
  ├─ 从 manager 获取 session
  └─ 通过 session.get_response() 流式返回
```

---

## 数据库表关系

```
Project (项目)
  ├─ business_requirement_file_id → File
  ├─ procurement_requirement_file_id → File
  └─ tender_document_file_id → File (最终使用的采购征询文件)

TenderGeneration (生成记录)
  ├─ project_id → Project
  ├─ business_requirement_file_id → File
  ├─ procurement_requirement_file_id → File
  ├─ file_id → File (生成的docx文件)
  └─ model_session → LLM Session ID

File (文件)
  └─ 存储所有文件记录
```

