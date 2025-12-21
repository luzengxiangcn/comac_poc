import api from './index'

/**
 * 生成采购征询文件
 * @param {number} projectId - 项目ID
 * @param {string} technicalRequirementFileId - 需求文档文件ID
 * @param {string} procurementRequirementFileId - 采购部门规范文档文件ID
 */
export const generateTender = (projectId, technicalRequirementFileId, procurementRequirementFileId) => {
  return api.post('/llm-tool/generate-tender', {
    project_id: projectId,
    technical_requirement_file_id: technicalRequirementFileId,
    procurement_requirement_file_id: procurementRequirementFileId
  })
}

/**
 * 获取项目的采购征询文件生成列表
 * @param {number} projectId - 项目ID
 */
export const getTenderGenerationList = (projectId) => {
  return api.get(`/llm-tool/tender-generation/${projectId}/list`)
}

/**
 * 使用生成的采购征询文件
 * @param {number} tenderGenerationId - 生成记录ID
 */
export const useTenderGeneration = (tenderGenerationId) => {
  return api.post(`/llm-tool/tender-generation/${tenderGenerationId}/use`)
}

/**
 * 删除采购征询文件生成记录
 * @param {number} tenderGenerationId - 生成记录ID
 */
export const deleteTenderGeneration = (tenderGenerationId) => {
  return api.delete(`/llm-tool/tender-generation/${tenderGenerationId}`)
}

/**
 * 获取项目的采购征询文件生成状态（已废弃，使用getTenderGenerationList代替）
 * @param {number} projectId - 项目ID
 */
export const getTenderGenerationStatus = (projectId) => {
  return api.get(`/llm-tool/tender-generation/${projectId}`)
}

/**
 * 获取采购征询文件生成的流式响应
 * @param {number} tenderGenerationId - 生成记录ID
 * @returns {Promise<Response>} Fetch Response 对象，用于流式读取
 */
export const getTenderGenerationStream = (tenderGenerationId) => {
  return fetch(`/api/llm-tool/tender-generation/${tenderGenerationId}/stream`, {
    headers: {
      'Accept': 'text/event-stream'
    }
  })
}

