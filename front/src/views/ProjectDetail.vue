<template>
  <div class="project-detail">
    <div class="header">
      <div class="header-content">
        <button class="back-btn" @click="goBack">← 返回</button>
        <h1>{{ projectName }}</h1>
      </div>
    </div>
    <div class="content-wrapper">
      <div class="layout-container">
        <div class="sidebar">
          <div
            class="sidebar-item"
            :class="{ active: activeTab === 'detail' }"
            @click="activeTab = 'detail'"
          >
            详情
          </div>
          <div
            class="sidebar-item"
            :class="{ active: activeTab === 'generate' }"
            @click="activeTab = 'generate'"
          >
            采购征询文件智能生成
          </div>
        </div>
        <div class="content-area">
          <!-- 详情Tab -->
          <div v-if="activeTab === 'detail'" class="detail-tab">
            <div class="detail-section">
              <h3 class="section-title">项目名称</h3>
              <div class="section-content project-name-section">
                <span class="project-name-text">{{ projectName }}</span>
                <button 
                  class="ai-rename-btn" 
                  @click="handleRenameProjectTitle"
                  :disabled="!canRenameProjectTitle || renamingProjectTitle"
                  :title="canRenameProjectTitle ? 'AI智能生成项目名称' : '请先上传需求文档或采购部门规范文档'"
                >
                  {{ renamingProjectTitle ? '生成中...' : 'AI改名' }}
                </button>
              </div>
            </div>
            
            <div class="detail-section">
              <h3 class="section-title">
                <span>
                  需求文档
                  <span 
                    v-if="collapsedBusinessRequirement" 
                    class="status-badge"
                    :class="{ 'status-completed': projectDetail.business_requirement_file_id, 'status-incomplete': !projectDetail.business_requirement_file_id }"
                  >
                    {{ projectDetail.business_requirement_file_id ? '完成' : '未完成' }}
                  </span>
                </span>
                <button class="collapse-btn" @click="collapsedBusinessRequirement = !collapsedBusinessRequirement">
                  {{ collapsedBusinessRequirement ? '展开' : '折叠' }}
                </button>
              </h3>
              <div class="section-content" :class="{ collapsed: collapsedBusinessRequirement }">
                <div class="document-header">
                  <input
                    ref="businessRequirementInput"
                    type="file"
                    accept=".doc,.docx"
                    @change="handleBusinessRequirementFileChange"
                    style="display: none"
                  />
                  <button class="upload-btn" @click="triggerBusinessRequirementInput" :disabled="uploadingBusinessRequirement">
                    {{ uploadingBusinessRequirement ? '上传中...' : (selectedBusinessRequirementFile ? '重新选择文件' : '上传文件') }}
                  </button>
                  <span v-if="selectedBusinessRequirementFile" class="file-name">{{ selectedBusinessRequirementFile.name }}</span>
                  <span v-if="uploadErrorBusinessRequirement" class="error-text">{{ uploadErrorBusinessRequirement }}</span>
                </div>
                <div class="document-body">
                  <DocumentViewer
                    v-if="businessRequirementDocument"
                    :content="businessRequirementDocument"
                    :loading="loadingBusinessRequirement"
                  />
                  <div v-else-if="loadingBusinessRequirement" class="loading">加载中...</div>
                  <div v-else-if="projectDetail.business_requirement_file_id" class="empty">无法加载文档</div>
                  <div v-else class="empty">暂无需求文档</div>
                </div>
              </div>
            </div>
            
            <div class="detail-section">
              <h3 class="section-title">
                <span>
                  采购部门规范文档
                  <span 
                    v-if="collapsedProcurementRequirement" 
                    class="status-badge"
                    :class="{ 'status-completed': projectDetail.procurement_requirement_file_id, 'status-incomplete': !projectDetail.procurement_requirement_file_id }"
                  >
                    {{ projectDetail.procurement_requirement_file_id ? '完成' : '未完成' }}
                  </span>
                </span>
                <button class="collapse-btn" @click="collapsedProcurementRequirement = !collapsedProcurementRequirement">
                  {{ collapsedProcurementRequirement ? '展开' : '折叠' }}
                </button>
              </h3>
              <div class="section-content" :class="{ collapsed: collapsedProcurementRequirement }">
                <div class="document-header">
                  <input
                    ref="procurementRequirementInput"
                    type="file"
                    accept=".doc,.docx"
                    @change="handleProcurementRequirementFileChange"
                    style="display: none"
                  />
                  <button class="upload-btn" @click="triggerProcurementRequirementInput" :disabled="uploadingProcurementRequirement">
                    {{ uploadingProcurementRequirement ? '上传中...' : (selectedProcurementRequirementFile ? '重新选择文件' : '上传文件') }}
                  </button>
                  <span v-if="selectedProcurementRequirementFile" class="file-name">{{ selectedProcurementRequirementFile.name }}</span>
                  <span v-if="uploadErrorProcurementRequirement" class="error-text">{{ uploadErrorProcurementRequirement }}</span>
                </div>
                <div class="document-body">
                  <DocumentViewer
                    v-if="procurementRequirementDocument"
                    :content="procurementRequirementDocument"
                    :loading="loadingProcurementRequirement"
                  />
                  <div v-else-if="loadingProcurementRequirement" class="loading">加载中...</div>
                  <div v-else-if="projectDetail.procurement_requirement_file_id" class="empty">无法加载文档</div>
                  <div v-else class="empty">暂无采购部门规范文档</div>
                </div>
              </div>
            </div>
            
            <div class="detail-section">
              <h3 class="section-title">
                <span>
                  采购征询文件
                  <span 
                    v-if="collapsedTenderDocument" 
                    class="status-badge"
                    :class="{ 'status-completed': projectDetail.tender_document_file_id, 'status-incomplete': !projectDetail.tender_document_file_id }"
                  >
                    {{ projectDetail.tender_document_file_id ? '完成' : '未完成' }}
                  </span>
                </span>
                <button class="collapse-btn" @click="collapsedTenderDocument = !collapsedTenderDocument">
                  {{ collapsedTenderDocument ? '展开' : '折叠' }}
                </button>
              </h3>
              <div class="section-content" :class="{ collapsed: collapsedTenderDocument }">
                <div class="document-header">
                  <input
                    ref="tenderDocumentInput"
                    type="file"
                    accept=".doc,.docx"
                    @change="handleTenderDocumentFileChange"
                    style="display: none"
                  />
                  <button class="upload-btn" @click="triggerTenderDocumentInput" :disabled="uploadingTenderDocument">
                    {{ uploadingTenderDocument ? '上传中...' : (selectedTenderDocumentFile ? '重新选择文件' : '上传文件') }}
                  </button>
                  <button 
                    v-if="canGenerateTender" 
                    class="generate-btn" 
                    @click="goToGenerateTab"
                  >
                    智能生成
                  </button>
                  <span v-if="selectedTenderDocumentFile" class="file-name">{{ selectedTenderDocumentFile.name }}</span>
                  <span v-if="uploadErrorTenderDocument" class="error-text">{{ uploadErrorTenderDocument }}</span>
                </div>
                <div class="document-body">
                  <DocumentViewer
                    v-if="tenderDocument"
                    :content="tenderDocument"
                    :loading="loadingDocument"
                  />
                  <div v-else-if="loadingDocument" class="loading">加载中...</div>
                  <div v-else-if="projectDetail.tender_document_file_id" class="empty">无法加载文档</div>
                  <div v-else class="empty">暂无采购征询文件</div>
                </div>
              </div>
            </div>
            
            <div class="detail-section">
              <h3 class="section-title">供应商列表</h3>
              <div class="section-content">
                <div class="supplier-actions">
                  <button class="btn btn-primary" @click="showBatchImportDialog = true">
                    批量导入
                  </button>
                  <button class="btn" @click="showAddDialog = true">
                    添加供应商
                  </button>
                </div>
                <div class="suppliers-grid">
                  <SupplierCard
                    v-for="bid in bidRecords"
                    :key="`${bid.bid_record_id || bid.project_id}-${bid.supplier_id || 'pending'}`"
                    :bid-record="bid"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <!-- 采购征询文件智能生成Tab -->
          <div v-if="activeTab === 'generate'" class="generate-tab">
            <div class="generation-list">
              <!-- 添加按钮 -->
              <div class="generation-item add-item" @click="handleAddGeneration">
                <div class="add-icon">+</div>
                <div class="add-text">新建生成</div>
              </div>
              
              <!-- 生成记录列表 -->
              <div 
                v-for="item in tenderGenerationList" 
                :key="item.tender_generation_id"
                class="generation-item"
              >
                <div class="generation-info">
                  <div class="generation-name">
                    {{ item.file_name || `生成记录 #${item.tender_generation_id}` }}
                  </div>
                  <div class="generation-status">
                    <span class="status-badge" :class="`status-${item.status}`">
                      {{ getStatusText(item.status) }}
                    </span>
                  </div>
                </div>
                <div class="generation-actions">
                  <button 
                    class="action-btn view-btn" 
                    @click="handleViewDetail(item)"
                  >
                    查看详情
                  </button>
                  <button 
                    v-if="item.status === 'finished' && item.file_id"
                    class="action-btn download-btn" 
                    @click="handleDownloadGeneration(item)"
                  >
                    下载
                  </button>
                  <button 
                    class="action-btn use-btn" 
                    @click="handleUseGeneration(item)"
                    :disabled="item.status !== 'finished'"
                  >
                    使用
                  </button>
                  <button 
                    class="action-btn delete-btn" 
                    @click="handleDeleteGeneration(item)"
                  >
                    删除
                  </button>
                </div>
              </div>
              
              <!-- 空状态 -->
              <div v-if="tenderGenerationList.length === 0 && !loadingGenerationList" class="empty-list">
                暂无生成记录，点击"+"按钮开始生成
              </div>
              
              <!-- 加载状态 -->
              <div v-if="loadingGenerationList" class="loading">加载中...</div>
            </div>
            
            <!-- 详情对话框 -->
            <div v-if="showDetailDialog" class="detail-dialog-overlay" @click="showDetailDialog = false">
              <div class="detail-dialog" @click.stop>
                <div class="dialog-header">
                  <h3>生成详情</h3>
                  <div class="dialog-header-right">
                    <span v-if="loadingDetail && !detailContent" class="generating-badge">生成中...</span>
                    <button class="close-btn" @click="showDetailDialog = false">×</button>
                  </div>
                </div>
                <div class="dialog-body">
                  <DocumentViewer
                    v-if="detailContent"
                    :content="detailContent"
                    :loading="loadingDetail"
                  />
                  <div v-else-if="loadingDetail" class="loading">正在生成，请稍候...</div>
                  <div v-else class="empty">暂无内容</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 添加供应商对话框 -->
    <AddSupplierDialog
      v-if="showAddDialog"
      :project-id="projectId"
      @close="showAddDialog = false"
      @success="handleAddSuccess"
    />
    <!-- 批量导入供应商对话框 -->
    <BatchImportSupplierDialog
      v-if="showBatchImportDialog"
      :project-id="projectId"
      @close="showBatchImportDialog = false"
      @success="handleBatchImportSuccess"
    />
    <!-- 通知组件 -->
    <Notification
      v-if="notification.visible"
      :message="notification.message"
      :type="notification.type"
      @close="notification.visible = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getProjectDetail, getFileContent, uploadProjectDocuments, downloadFile, renameProjectTitle } from '../api/project'
import { getBidRecords } from '../api/bid'
import { generateTender, getTenderGenerationList, useTenderGeneration, deleteTenderGeneration, getTenderGenerationStream } from '../api/llm'
import SupplierCard from '../components/SupplierCard.vue'
import AddSupplierDialog from '../components/AddSupplierDialog.vue'
import BatchImportSupplierDialog from '../components/BatchImportSupplierDialog.vue'
import DocumentViewer from '../components/DocumentViewer.vue'
import Notification from '../components/Notification.vue'

export default {
  name: 'ProjectDetail',
  components: {
    SupplierCard,
    AddSupplierDialog,
    BatchImportSupplierDialog,
    DocumentViewer,
    Notification
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const projectId = computed(() => parseInt(route.params.id))
    
    const projectName = ref('')
    const projectDetail = ref({})
    const activeTab = ref('detail')
    const bidRecords = ref([])
    const tenderDocument = ref('')
    const loadingDocument = ref(false)
    const businessRequirementDocument = ref('')
    const loadingBusinessRequirement = ref(false)
    const procurementRequirementDocument = ref('')
    const loadingProcurementRequirement = ref(false)
    const showAddDialog = ref(false)
    const showBatchImportDialog = ref(false)
    
    // 文件上传相关
    const businessRequirementInput = ref(null)
    const procurementRequirementInput = ref(null)
    const tenderDocumentInput = ref(null)
    const selectedBusinessRequirementFile = ref(null)
    const selectedProcurementRequirementFile = ref(null)
    const selectedTenderDocumentFile = ref(null)
    const uploadingBusinessRequirement = ref(false)
    const uploadingProcurementRequirement = ref(false)
    const uploadingTenderDocument = ref(false)
    const uploadErrorBusinessRequirement = ref('')
    const uploadErrorProcurementRequirement = ref('')
    const uploadErrorTenderDocument = ref('')
    
    // 折叠状态
    const collapsedBusinessRequirement = ref(false)
    const collapsedProcurementRequirement = ref(false)
    const collapsedTenderDocument = ref(false)
    
    // 采购征询文件生成相关
    const generatingTender = ref(false)
    const tenderGenerationStatus = ref(null)
    const tenderGenerationId = ref(null)
    const generatedTenderContent = ref('')
    const loadingGeneratedTender = ref(false)
    
    // 生成列表相关
    const tenderGenerationList = ref([])
    const loadingGenerationList = ref(false)
    const showDetailDialog = ref(false)
    const detailContent = ref('')
    const loadingDetail = ref(false)
    const currentDetailId = ref(null)
    
    // 判断是否可以生成采购征询文件
    const canGenerateTender = computed(() => {
      return projectDetail.value.business_requirement_file_id && 
             projectDetail.value.procurement_requirement_file_id
    })
    
    // 判断是否可以AI改名（需求文档或采购部门规范文档至少有一个）
    const canRenameProjectTitle = computed(() => {
      return projectDetail.value.business_requirement_file_id || 
             projectDetail.value.procurement_requirement_file_id
    })
    
    // AI改名相关
    const renamingProjectTitle = ref(false)
    
    // 通知相关
    const notification = ref({
      visible: false,
      message: '',
      type: 'success'
    })
    
    const showNotification = (message, type = 'success') => {
      notification.value = {
        visible: true,
        message,
        type
      }
    }

    const fetchProjectDetail = async () => {
      try {
        const data = await getProjectDetail(projectId.value)
        projectDetail.value = data
        projectName.value = data.name || '项目详情'
      } catch (err) {
        console.error('Failed to fetch project detail:', err)
        projectName.value = '项目详情'
      }
    }

    const fetchTenderDocument = async () => {
      // 如果 projectDetail 还没有加载，先加载它
      if (!projectDetail.value.id) {
        await fetchProjectDetail()
      }
      if (!projectDetail.value.tender_document_file_id) {
        return
      }
      try {
        loadingDocument.value = true
        const data = await getFileContent(projectDetail.value.tender_document_file_id)
        tenderDocument.value = data.content || data || ''
      } catch (err) {
        console.error('Failed to fetch tender document:', err)
        tenderDocument.value = ''
      } finally {
        loadingDocument.value = false
      }
    }

    const fetchBusinessRequirementDocument = async () => {
      // 如果 projectDetail 还没有加载，先加载它
      if (!projectDetail.value.id) {
        await fetchProjectDetail()
      }
      if (!projectDetail.value.business_requirement_file_id) {
        return
      }
      try {
        loadingBusinessRequirement.value = true
        const data = await getFileContent(projectDetail.value.business_requirement_file_id)
        businessRequirementDocument.value = data.content || data || ''
      } catch (err) {
        console.error('Failed to fetch business requirement document:', err)
        businessRequirementDocument.value = ''
      } finally {
        loadingBusinessRequirement.value = false
      }
    }

    const fetchProcurementRequirementDocument = async () => {
      // 如果 projectDetail 还没有加载，先加载它
      if (!projectDetail.value.id) {
        await fetchProjectDetail()
      }
      if (!projectDetail.value.procurement_requirement_file_id) {
        return
      }
      try {
        loadingProcurementRequirement.value = true
        const data = await getFileContent(projectDetail.value.procurement_requirement_file_id)
        procurementRequirementDocument.value = data.content || data || ''
      } catch (err) {
        console.error('Failed to fetch procurement requirement document:', err)
        procurementRequirementDocument.value = ''
      } finally {
        loadingProcurementRequirement.value = false
      }
    }

    const fetchBidRecords = async () => {
      try {
        const data = await getBidRecords(projectId.value)
        bidRecords.value = Array.isArray(data) ? data : []
      } catch (err) {
        console.error('Failed to fetch bid records:', err)
        bidRecords.value = []
      }
    }

    const handleAddSuccess = () => {
      showAddDialog.value = false
      fetchBidRecords()
    }

    const handleBatchImportSuccess = () => {
      showBatchImportDialog.value = false
      fetchBidRecords()
    }

    const goBack = () => {
      router.push('/')
    }

    // 文件上传相关函数
    const triggerBusinessRequirementInput = () => {
      businessRequirementInput.value?.click()
    }

    const triggerProcurementRequirementInput = () => {
      procurementRequirementInput.value?.click()
    }

    const triggerTenderDocumentInput = () => {
      tenderDocumentInput.value?.click()
    }

    const handleBusinessRequirementFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      const ext = file.name.split('.').pop().toLowerCase()
      if (!['doc', 'docx'].includes(ext)) {
        uploadErrorBusinessRequirement.value = '文件必须是 .doc 或 .docx 格式'
        return
      }
      
      selectedBusinessRequirementFile.value = file
      uploadErrorBusinessRequirement.value = ''
      
      try {
        uploadingBusinessRequirement.value = true
        await uploadProjectDocuments(
          projectId.value,
          file,
          null,
          null
        )
        // 上传成功后重新加载项目详情和文档
        await fetchProjectDetail()
        await fetchBusinessRequirementDocument()
        selectedBusinessRequirementFile.value = null
        event.target.value = ''
      } catch (err) {
        uploadErrorBusinessRequirement.value = err.response?.data?.detail || err.message || '上传失败'
      } finally {
        uploadingBusinessRequirement.value = false
      }
    }

    const handleProcurementRequirementFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      const ext = file.name.split('.').pop().toLowerCase()
      if (!['doc', 'docx'].includes(ext)) {
        uploadErrorProcurementRequirement.value = '文件必须是 .doc 或 .docx 格式'
        return
      }
      
      selectedProcurementRequirementFile.value = file
      uploadErrorProcurementRequirement.value = ''
      
      try {
        uploadingProcurementRequirement.value = true
        await uploadProjectDocuments(
          projectId.value,
          null,
          file,
          null
        )
        // 上传成功后重新加载项目详情和文档
        await fetchProjectDetail()
        await fetchProcurementRequirementDocument()
        selectedProcurementRequirementFile.value = null
        event.target.value = ''
      } catch (err) {
        uploadErrorProcurementRequirement.value = err.response?.data?.detail || err.message || '上传失败'
      } finally {
        uploadingProcurementRequirement.value = false
      }
    }

    const handleTenderDocumentFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      const ext = file.name.split('.').pop().toLowerCase()
      if (!['doc', 'docx'].includes(ext)) {
        uploadErrorTenderDocument.value = '文件必须是 .doc 或 .docx 格式'
        return
      }
      
      selectedTenderDocumentFile.value = file
      uploadErrorTenderDocument.value = ''
      
      try {
        uploadingTenderDocument.value = true
        await uploadProjectDocuments(
          projectId.value,
          null,
          null,
          file
        )
        // 上传成功后重新加载项目详情和文档
        await fetchProjectDetail()
        await fetchTenderDocument()
        selectedTenderDocumentFile.value = null
        event.target.value = ''
      } catch (err) {
        uploadErrorTenderDocument.value = err.response?.data?.detail || err.message || '上传失败'
      } finally {
        uploadingTenderDocument.value = false
      }
    }

    // 获取生成状态文本
    const getStatusText = (status) => {
      if (!status) return '未开始'
      const statusMap = {
        'running': '生成中',
        'finished': '已完成',
        'failed': '生成失败'
      }
      return statusMap[status] || status
    }

    // 流式读取生成内容（保留用于兼容）
    const streamGeneratedTenderContent = async (generationId) => {
      // 此方法已不再使用，保留用于兼容
      console.log('streamGeneratedTenderContent is deprecated')
    }

    // 跳转到生成标签页
    const goToGenerateTab = () => {
      activeTab.value = 'generate'
    }

    // 获取生成列表
    const fetchTenderGenerationList = async () => {
      try {
        loadingGenerationList.value = true
        const data = await getTenderGenerationList(projectId.value)
        tenderGenerationList.value = data.list || []
      } catch (err) {
        console.error('Failed to fetch tender generation list:', err)
        tenderGenerationList.value = []
      } finally {
        loadingGenerationList.value = false
      }
    }

    // 添加生成（点击+按钮）
    const handleAddGeneration = async () => {
      // 验证两个需求文件是否存在
      if (!projectDetail.value.business_requirement_file_id) {
        alert('请先上传业务需求文件')
        return
      }
      if (!projectDetail.value.procurement_requirement_file_id) {
        alert('请先上传采购部门要求文件')
        return
      }
      
      try {
        generatingTender.value = true
        const data = await generateTender(
          projectId.value,
          projectDetail.value.business_requirement_file_id,
          projectDetail.value.procurement_requirement_file_id
        )
        
        // 刷新列表
        await fetchTenderGenerationList()
      } catch (err) {
        console.error('Failed to generate tender:', err)
        alert(err.response?.data?.detail || err.message || '生成采购征询文件失败')
      } finally {
        generatingTender.value = false
      }
    }

    // 查看详情
    const handleViewDetail = async (item) => {
      try {
        showDetailDialog.value = true
        loadingDetail.value = true
        detailContent.value = ''
        currentDetailId.value = item.tender_generation_id
        
        // 如果状态是running，使用流式接口查看生成过程
        if (item.status === 'running') {
          await streamDetailContent(item.tender_generation_id)
        } else if (item.file_id) {
          // 如果已完成，直接加载文件内容
          const fileData = await getFileContent(item.file_id)
          detailContent.value = fileData.content || fileData || ''
          loadingDetail.value = false
        } else {
          alert('该记录没有生成文件')
          loadingDetail.value = false
          showDetailDialog.value = false
        }
      } catch (err) {
        console.error('Failed to load detail:', err)
        alert('加载详情失败')
        detailContent.value = ''
        loadingDetail.value = false
      }
    }

    // 流式读取详情内容
    const streamDetailContent = async (generationId) => {
      try {
        loadingDetail.value = true
        detailContent.value = ''
        
        // 使用封装的流式接口
        const response = await getTenderGenerationStream(generationId)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留最后不完整的行
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                if (data.type === 'chunk' && data.content) {
                  // 实时追加内容
                  detailContent.value += data.content
                  loadingDetail.value = false // 有内容后就不再显示loading
                } else if (data.type === 'content' && data.content) {
                  // 完整内容
                  detailContent.value = data.content
                  loadingDetail.value = false
                  if (data.status === 'finished') {
                    // 生成完成，刷新列表
                    await fetchTenderGenerationList()
                  }
                } else if (data.type === 'status') {
                  if (data.status === 'finished') {
                    // 生成完成，重新获取文件内容
                    loadingDetail.value = true
                    // 刷新列表以获取最新的file_id
                    await fetchTenderGenerationList()
                    // 从列表中获取最新的记录
                    const updatedList = await getTenderGenerationList(projectId.value)
                    const updatedItem = updatedList.list.find(
                      item => item.tender_generation_id === generationId
                    )
                    if (updatedItem && updatedItem.file_id) {
                      try {
                        const fileData = await getFileContent(updatedItem.file_id)
                        detailContent.value = fileData.content || fileData || ''
                      } catch (err) {
                        console.error('Failed to load finished content:', err)
                      }
                    }
                    loadingDetail.value = false
                  } else if (data.status === 'failed') {
                    loadingDetail.value = false
                    alert('生成失败')
                  }
                } else if (data.type === 'error') {
                  console.error('Stream error:', data.error)
                  loadingDetail.value = false
                  alert(`生成错误: ${data.error}`)
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', e, line)
              }
            }
          }
        }
        
        // 处理剩余的buffer
        if (buffer.trim()) {
          if (buffer.startsWith('data: ')) {
            try {
              const data = JSON.parse(buffer.slice(6))
              if (data.type === 'chunk' && data.content) {
                detailContent.value += data.content
                loadingDetail.value = false
              }
            } catch (e) {
              console.error('Failed to parse remaining buffer:', e)
            }
          }
        }
      } catch (err) {
        console.error('Failed to stream detail content:', err)
        loadingDetail.value = false
        alert('加载详情失败: ' + (err.message || '未知错误'))
      }
    }

    // 使用生成的文件
    const handleUseGeneration = async (item) => {
      if (item.status !== 'finished') {
        alert('只有已完成的生成记录才能使用')
        return
      }
      
      if (!confirm('确定要使用此生成文件吗？这将替换项目当前的采购征询文件。')) {
        return
      }
      
      try {
        await useTenderGeneration(item.tender_generation_id)
        alert('已成功使用该生成文件')
        // 刷新项目详情
        await fetchProjectDetail()
        await fetchTenderDocument()
      } catch (err) {
        console.error('Failed to use generation:', err)
        alert(err.response?.data?.detail || err.message || '使用失败')
      }
    }

    // 下载生成的文件
    const handleDownloadGeneration = async (item) => {
      if (item.status !== 'finished' || !item.file_id) {
        alert('该记录没有可下载的文件')
        return
      }
      
      try {
        downloadFile(item.file_id, item.file_name || '采购征询文件.docx')
      } catch (err) {
        console.error('Failed to download file:', err)
        alert(err.response?.data?.detail || err.message || '下载失败')
      }
    }

    // 删除生成记录
    const handleDeleteGeneration = async (item) => {
      if (!confirm('确定要删除此生成记录吗？')) {
        return
      }
      
      try {
        await deleteTenderGeneration(item.tender_generation_id)
        // 刷新列表
        await fetchTenderGenerationList()
      } catch (err) {
        console.error('Failed to delete generation:', err)
        alert(err.response?.data?.detail || err.message || '删除失败')
      }
    }

    // 生成采购征询文件（保留用于兼容）
    const handleGenerateTender = async () => {
      if (!canGenerateTender.value) {
        return
      }
      
      try {
        generatingTender.value = true
        const data = await generateTender(
          projectId.value,
          projectDetail.value.business_requirement_file_id,
          projectDetail.value.procurement_requirement_file_id
        )
        
        tenderGenerationId.value = data.tender_generation_id
        tenderGenerationStatus.value = data.status
        
        // 跳转到生成页面
        activeTab.value = 'generate'
        
        // 刷新列表
        await fetchTenderGenerationList()
      } catch (err) {
        console.error('Failed to generate tender:', err)
        alert(err.response?.data?.detail || err.message || '生成采购征询文件失败')
      } finally {
        generatingTender.value = false
      }
    }

    const handleRenameProjectTitle = async () => {
      if (!canRenameProjectTitle.value || renamingProjectTitle.value) {
        return
      }
      
      try {
        renamingProjectTitle.value = true
        const response = await renameProjectTitle(projectId.value)
        const newName = response.data?.name || response.name
        
        if (newName) {
          // 更新本地状态
          projectName.value = newName
          projectDetail.value.name = newName
          // 重新获取项目详情以确保数据同步
          await fetchProjectDetail()
          // 显示成功通知
          showNotification(`项目名称已更新为：${newName}`, 'success')
        }
      } catch (err) {
        console.error('Failed to rename project title:', err)
        const errorMsg = err.response?.data?.detail || err.message || 'AI生成项目名称失败'
        showNotification(errorMsg, 'error')
      } finally {
        renamingProjectTitle.value = false
      }
    }

    onMounted(async () => {
      await fetchProjectDetail()
      await fetchBidRecords()
      // 默认加载详情页面的内容
      if (activeTab.value === 'detail') {
        await fetchBusinessRequirementDocument()
        await fetchProcurementRequirementDocument()
        await fetchTenderDocument()
      } else if (activeTab.value === 'tender') {
        await fetchTenderDocument()
      } else if (activeTab.value === 'generate') {
        await fetchTenderGenerationList()
      }
    })

    return {
      projectId,
      projectName,
      projectDetail,
      activeTab,
      bidRecords,
      tenderDocument,
      loadingDocument,
      businessRequirementDocument,
      loadingBusinessRequirement,
      procurementRequirementDocument,
      loadingProcurementRequirement,
      showAddDialog,
      showBatchImportDialog,
      handleAddSuccess,
      handleBatchImportSuccess,
      goBack,
      fetchTenderDocument,
      fetchBusinessRequirementDocument,
      fetchProcurementRequirementDocument,
      businessRequirementInput,
      procurementRequirementInput,
      tenderDocumentInput,
      selectedBusinessRequirementFile,
      selectedProcurementRequirementFile,
      selectedTenderDocumentFile,
      uploadingBusinessRequirement,
      uploadingProcurementRequirement,
      uploadingTenderDocument,
      uploadErrorBusinessRequirement,
      uploadErrorProcurementRequirement,
      uploadErrorTenderDocument,
      triggerBusinessRequirementInput,
      triggerProcurementRequirementInput,
      triggerTenderDocumentInput,
      handleBusinessRequirementFileChange,
      handleProcurementRequirementFileChange,
      handleTenderDocumentFileChange,
      collapsedBusinessRequirement,
      collapsedProcurementRequirement,
      collapsedTenderDocument,
      generatingTender,
      tenderGenerationStatus,
      tenderGenerationId,
      generatedTenderContent,
      loadingGeneratedTender,
      canGenerateTender,
      handleGenerateTender,
      streamGeneratedTenderContent,
      getStatusText,
      // 新增的生成列表相关
      tenderGenerationList,
      loadingGenerationList,
      showDetailDialog,
      detailContent,
      loadingDetail,
      goToGenerateTab,
      fetchTenderGenerationList,
      handleAddGeneration,
      handleViewDetail,
      // AI改名相关
      canRenameProjectTitle,
      renamingProjectTitle,
      handleRenameProjectTitle,
      // 通知相关
      notification,
      handleDownloadGeneration,
      handleUseGeneration,
      handleDeleteGeneration
    }
  },
  watch: {
    activeTab(newVal) {
      if (newVal === 'detail') {
        if (!this.businessRequirementDocument && !this.loadingBusinessRequirement) {
          this.fetchBusinessRequirementDocument()
        }
        if (!this.procurementRequirementDocument && !this.loadingProcurementRequirement) {
          this.fetchProcurementRequirementDocument()
        }
        if (!this.tenderDocument && !this.loadingDocument) {
          this.fetchTenderDocument()
        }
      } else if (newVal === 'generate') {
        this.fetchTenderGenerationList()
      }
    }
  }
}
</script>

<style scoped>
.project-detail {
  min-height: 100vh;
  background-color: var(--bg-color);
}

.header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 32px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: var(--primary-color);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.back-btn:hover {
  background-color: var(--bg-color);
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 32px 32px;
}

.layout-container {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.sidebar {
  width: 200px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 8px 0;
  flex-shrink: 0;
}

.sidebar-item {
  padding: 16px 24px;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-secondary);
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.sidebar-item:hover {
  color: var(--primary-color);
  background-color: #f0f9ff;
}

.sidebar-item.active {
  color: var(--primary-color);
  background-color: #f0f9ff;
  border-left-color: var(--primary-color);
  font-weight: 600;
}

.content-area {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  min-height: 600px;
  padding: 24px;
}

.detail-tab {
  height: 100%;
}

.detail-section {
  margin-bottom: 32px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-content {
  color: var(--text-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  background-color: #fafafa;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.project-name-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.project-name-text {
  flex: 1;
  word-break: break-word;
}

.ai-rename-btn {
  padding: 6px 16px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  white-space: nowrap;
  flex-shrink: 0;
}

.ai-rename-btn:hover:not(:disabled) {
  background-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.ai-rename-btn:disabled {
  background-color: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
}

.section-content.collapsed .document-body {
  display: none;
}

.document-body {
  transition: opacity 0.3s ease;
}

.tender-tab {
  height: 100%;
}

.supplier-tab {
  height: 100%;
}

.supplier-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.suppliers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.add-supplier-card {
  min-height: 150px;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fafafa;
}

.add-supplier-card:hover {
  border-color: var(--primary-color);
  background-color: #f0f9ff;
}

.add-icon {
  font-size: 48px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.add-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  background-color: white;
  border-radius: 4px;
  margin-top: 16px;
}

.document-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  border-bottom: 2px solid var(--border-color);
  background-color: white;
  border-radius: 4px 4px 0 0;
  margin: -20px -20px 16px -20px;
}

.upload-btn {
  padding: 8px 16px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.upload-btn:hover:not(:disabled) {
  background-color: #0284c7;
}

.upload-btn:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
}

.file-name {
  color: var(--text-primary);
  font-size: 14px;
  flex: 1;
}

.error-text {
  color: var(--danger-color);
  font-size: 14px;
}

.collapse-btn {
  padding: 4px 12px;
  background-color: transparent;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.collapse-btn:hover {
  background-color: var(--primary-color);
  color: white;
}

.status-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-completed {
  background-color: #d4edda;
  color: #155724;
}

.status-incomplete {
  background-color: #f8d7da;
  color: #721c24;
}

.generate-btn {
  padding: 8px 16px;
  background-color: var(--success-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.generate-btn:hover:not(:disabled) {
  background-color: #85ce61;
}

.generate-btn:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
}

.generate-tab {
  height: 100%;
}

.generate-section {
  margin-bottom: 32px;
}

.generate-section:last-child {
  margin-bottom: 0;
}

.status-content {
  padding: 16px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid var(--border-color);
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-weight: 600;
  color: var(--text-primary);
}

.status-value {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.status-none {
  color: var(--text-secondary);
  background-color: #f5f7fa;
}

.status-running {
  color: var(--warning-color);
  background-color: #fdf6ec;
}

.status-finished {
  color: var(--success-color);
  background-color: #f0f9ff;
}

.status-failed {
  color: var(--danger-color);
  background-color: #fef0f0;
}

.generate-tip {
  margin-top: 16px;
  padding: 12px;
  background-color: #f0f9ff;
  border-left: 4px solid var(--primary-color);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 14px;
}

.empty.error {
  color: var(--danger-color);
}

/* 生成列表样式 */
.generation-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.generation-item {
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  background-color: white;
  transition: all 0.3s;
}

.generation-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.generation-item.add-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 150px;
  cursor: pointer;
  border-style: dashed;
  background-color: #fafafa;
}

.generation-item.add-item:hover {
  border-color: var(--primary-color);
  background-color: #f0f9ff;
}

.add-icon {
  font-size: 48px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.add-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.generation-info {
  margin-bottom: 16px;
}

.generation-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.generation-status {
  display: flex;
  align-items: center;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.status-running {
  color: var(--warning-color);
  background-color: #fdf6ec;
}

.status-badge.status-finished {
  color: var(--success-color);
  background-color: #f0f9ff;
}

.status-badge.status-failed {
  color: var(--danger-color);
  background-color: #fef0f0;
}

.generation-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.view-btn {
  background-color: var(--primary-color);
  color: white;
}

.view-btn:hover:not(:disabled) {
  background-color: #0284c7;
}

.download-btn {
  background-color: #3b82f6;
  color: white;
}

.download-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.use-btn {
  background-color: var(--success-color);
  color: white;
}

.use-btn:hover:not(:disabled) {
  background-color: #85ce61;
}

.delete-btn {
  background-color: var(--danger-color);
  color: white;
}

.delete-btn:hover:not(:disabled) {
  background-color: #f56565;
}

.empty-list {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

/* 详情对话框样式 */
.detail-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.detail-dialog {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  padding: 20px 24px;
  border-bottom: 2px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.generating-badge {
  padding: 4px 12px;
  background-color: #fdf6ec;
  color: var(--warning-color);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.close-btn:hover {
  background-color: #f5f5f5;
  color: var(--text-primary);
}

.dialog-body {
  padding: 24px;
  overflow-y: auto;
  overflow-x: auto;
  flex: 1;
}

.dialog-body :deep(.document-content) {
  max-height: none;
}

.dialog-body :deep(table.markdown-table) {
  min-width: 100%;
  display: table;
}
</style>
