## 项目
每条记录代表一次采购项目
有如下字段：
1. id（key）
2. 名称 （默认：未命名）
3. 业务需求文件_id (可以为null)
4. 采购部门要求_id (可以为null)
5. 采购征询文件 null or file_id
6. AI评审_session_id

##  生成采购征询文件
1. id(key)
2. 业务需求文件_id
3. 采购部门要求_id
2. 项目id (foreign key, not null)
3. File_id (foreign key,  can be null)
6. model_session
7. status: running， finised, failed


## 供应商
1. id
2. 名称
3. 社会信用代码


## 投标记录
项目（外键）
供应商（外键，可以未空）
投标文件 （null or file_id， 外键）
身份识别_model_session
AI初审（json）
AI初审_model_session
AI初审成功 False, True (null, 默认)
人工初审（json）
AI评审 （json）
AI评审成功 False, True(null, 默认)

投标文件入库时间


## 文件（用来上传或下载文件）
file_id(primary key)
origin_name (上传文件的名称)
file_name （保存文件的uuid）
