import api from './index'

/**
 * 获取项目的投标记录列表（即供应商列表）
 * @param {number} projectId - 项目ID
 */
export const getBidRecords = (projectId) => {
  return api.get(`/bid/`, {
    params: { project_id: projectId }
  })
}

/**
 * 更新投标记录（部分字段）
 * @param {number} projectId - 项目ID
 * @param {number} supplierId - 供应商ID
 * @param {object} data - 要更新的字段（同后端 BidRecordUpdateRequest）
 */
export const updateBidRecord = (projectId, supplierId, data) => {
  return api.patch(`/bid/${projectId}/${supplierId}`, data)
}

/**
 * 创建投标记录（添加供应商）
 * @param {number} projectId - 项目ID
 * @param {string} name - 供应商名称
 * @param {string} registrationNumber - 社会信用代码
 * @param {File} file - 投标文件（可选）
 */
export const createBidRecord = (projectId, name, registrationNumber, file = null) => {
  const formData = new FormData()
  formData.append('project_id', projectId)
  formData.append('name', name)
  formData.append('registration_number', registrationNumber)
  if (file) {
    formData.append('file', file)
  }
  return api.post('/bid/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
