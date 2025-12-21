import api from './index'

/**
 * 批量导入供应商（上传多个投标文件，自动识别供应商信息）
 * @param {number} projectId - 项目ID
 * @param {File[]} files - 投标文件列表（多个文件）
 */
export const batchImportSuppliers = (projectId, files) => {
  const formData = new FormData()
  formData.append('project_id', projectId)
  
  // 确保所有文件都被添加
  console.log(`[批量导入] 准备上传 ${files.length} 个文件`)
  files.forEach((file, index) => {
    console.log(`[批量导入] 添加文件 ${index + 1}: ${file.name}`)
    formData.append('files', file)
  })
  
  // 验证 FormData 中的文件数量
  const fileEntries = Array.from(formData.entries()).filter(([key]) => key === 'files')
  console.log(`[批量导入] FormData 中实际包含 ${fileEntries.length} 个文件`)
  
  // 注意：不要手动设置 Content-Type，让浏览器自动设置（包含 boundary）
  // 如果手动设置 Content-Type，会覆盖掉浏览器自动添加的 boundary，导致文件上传失败
  return api.post('/supplier/batch-import', formData)
}

/**
 * 查询批量导入状态
 * @param {number} projectId - 项目ID
 */
export const getBatchImportStatus = (projectId) => {
  return api.get(`/supplier/batch-import/${projectId}/status`)
}

