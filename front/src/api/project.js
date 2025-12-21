import api from './index'

/**
 * 获取项目列表
 */
export const getProjects = () => {
  return api.get('/project/')
}

/**
 * 获取项目详情
 * @param {number} id - 项目ID
 */
export const getProjectDetail = (id) => {
  return api.get(`/project/${id}`)
}

/**
 * 创建项目
 * @param {string} name - 项目名称（可选）
 * @param {File} file - 采购征询文件（可选）
 * @param {File} businessRequirementFile - 需求文档（可选）
 * @param {File} procurementRequirementFile - 采购部门规范文档（可选）
 */
export const createProject = (name = null, file = null, businessRequirementFile = null, procurementRequirementFile = null) => {
  const formData = new FormData()
  if (name) {
    formData.append('name', name)
  }
  if (file) {
    formData.append('file', file)
  }
  if (businessRequirementFile) {
    formData.append('business_requirement_file', businessRequirementFile)
  }
  if (procurementRequirementFile) {
    formData.append('procurement_requirement_file', procurementRequirementFile)
  }
  return api.post('/project/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取项目采购征询文件内容（Markdown格式）
 * @param {number} id - 项目ID
 */
export const getProjectTenderDocument = (id) => {
  return api.get(`/project/${id}/tender-document`)
}

/**
 * 获取文件内容（Markdown格式）
 * @param {string} fileId - 文件ID
 */
export const getFileContent = (fileId) => {
  return api.get(`/project/file/${fileId}/content`)
}

/**
 * 下载文件
 * @param {string} fileId - 文件ID
 * @param {string} fileName - 文件名（可选，用于设置下载文件名）
 */
export const downloadFile = (fileId, fileName) => {
  const url = `/api/project/file/${fileId}/download`
  const link = document.createElement('a')
  link.href = url
  if (fileName) {
    link.download = fileName
  }
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 上传项目文档
 * @param {number} projectId - 项目ID
 * @param {File} businessRequirementFile - 需求文档（可选）
 * @param {File} procurementRequirementFile - 采购部门规范文档（可选）
 * @param {File} tenderDocumentFile - 采购征询文件（可选）
 */
export const uploadProjectDocuments = (
  projectId,
  businessRequirementFile = null,
  procurementRequirementFile = null,
  tenderDocumentFile = null
) => {
  const formData = new FormData()
  if (businessRequirementFile) {
    formData.append('business_requirement_file', businessRequirementFile)
  }
  if (procurementRequirementFile) {
    formData.append('procurement_requirement_file', procurementRequirementFile)
  }
  if (tenderDocumentFile) {
    formData.append('tender_document_file', tenderDocumentFile)
  }
  return api.post(`/project/${projectId}/upload-documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * AI重命名项目标题
 * @param {number} projectId - 项目ID
 */
export const renameProjectTitle = (projectId) => {
  return api.post(`/llm-rename/rename-project-title/${projectId}`)
}

/**
 * 删除项目
 * @param {number} projectId - 项目ID
 */
export const deleteProject = (projectId) => {
  return api.delete(`/project/${projectId}`)
}
