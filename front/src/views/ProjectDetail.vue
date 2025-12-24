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
          <div
            class="sidebar-item"
            :class="{ active: activeTab === 'preliminary' }"
            @click="activeTab = 'preliminary'"
          >
            初审
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
              <h3 class="section-title">
                <span>供应商列表</span>
                <button 
                  class="refresh-btn" 
                  @click="handleRefreshSuppliers"
                  :disabled="refreshingSuppliers"
                  title="手动刷新供应商列表"
                >
                  {{ refreshingSuppliers ? '刷新中...' : '刷新' }}
                </button>
              </h3>
              <div class="section-content">
                <div class="supplier-actions">
                  <button class="btn btn-primary" @click="showBatchImportDialog = true">
                    批量导入
                  </button>
                </div>
                <div class="suppliers-grid">
                  <SupplierCard
                    v-for="bid in bidRecords"
                    :key="`${bid.bid_record_id || bid.project_id}-${bid.supplier_id || 'pending'}`"
                    :bid-record="bid"
                  />
                  <div class="add-supplier-card" @click="showAddDialog = true">
                    <div class="add-icon">+</div>
                    <div class="add-text">添加供应商</div>
                  </div>
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

          <!-- 初审Tab -->
          <div v-if="activeTab === 'preliminary'" class="preliminary-tab">
            <div class="detail-section">
              <h3 class="section-title">
                <span>供应商初审</span>
              </h3>
              <div class="section-content preliminary-content">
                <div v-if="bidRecords.length" class="suppliers-grid preliminary-suppliers-grid">
                  <SupplierCard
                    v-for="bid in bidRecords"
                    :key="`${bid.bid_record_id || bid.project_id}-${bid.supplier_id || 'pending'}`"
                    :bid-record="bid"
                    :clickable="true"
                    :selected="selectedBidRecord && selectedBidRecord.bid_record_id === bid.bid_record_id"
                    @select="handleSelectBidRecord"
                    @ai-preliminary-click="handleAiPreliminaryClick"
                  />
                </div>
                <div v-else class="empty">
                  暂无供应商，请先在"详情"页添加供应商
                </div>

                <div v-if="bidRecords.length" class="preliminary-actions">
                  <button
                    class="ai-review-btn"
                    :disabled="aiPreliminaryReviewing"
                    @click="handleAiPreliminaryReview"
                  >
                    {{ aiPreliminaryReviewing ? 'AI初评中...' : '一键AI初评' }}
                  </button>
                  <div v-if="aiPreliminaryStatus" class="ai-review-status">
                    <div class="status-summary">
                      <span>总计: {{ aiPreliminaryStatus.total || 0 }}</span>
                      <span class="status-success">成功: {{ aiPreliminaryStatus.success_count || 0 }}</span>
                      <span class="status-failed">失败: {{ aiPreliminaryStatus.failed_count || 0 }}</span>
                      <span class="status-processing">处理中: {{ aiPreliminaryStatus.processing_count || 0 }}</span>
                      <span class="status-pending">待处理: {{ aiPreliminaryStatus.pending_count || 0 }}</span>
                    </div>
                  </div>
                </div>

                <div v-if="selectedBidRecord" class="preliminary-detail">
                  <h4 class="preliminary-detail-title">
                    当前供应商：{{ selectedBidRecord.supplier?.name || '未知供应商' }}
                  </h4>
                  <div class="preliminary-detail-body">
                    <div class="preliminary-row">
                      <span class="label">初审结果：</span>
                      <div class="value preliminary-status-edit">
                        <select
                          v-model="manualPreliminaryStatus"
                          class="status-select"
                        >
                          <option value="null">未开始</option>
                          <option value="true">通过</option>
                          <option value="false">不通过</option>
                        </select>
                      </div>
                    </div>
                    <div class="preliminary-row">
                      <span class="label">理由：</span>
                      <div class="value preliminary-reason-edit">
                        <div v-if="isReasonFromAI(selectedBidRecord)" class="ai-reason-notice">
                          <span class="ai-notice-icon">🤖</span>
                          <span class="ai-notice-text">当前显示的是AI初审结果，请人工审核确认</span>
                        </div>
                        <textarea
                          v-model="manualPreliminaryReason"
                          rows="5"
                          placeholder="请输入初审理由"
                          class="reason-textarea"
                          :class="{ 'ai-reason-textarea': isReasonFromAI(selectedBidRecord) }"
                        ></textarea>
                        <div class="preliminary-save-actions">
                          <button
                            class="primary-btn"
                            :disabled="savingPreliminary"
                            @click="handleSavePreliminary"
                          >
                            {{ savingPreliminary ? '保存中...' : '确定' }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else-if="bidRecords.length" class="empty">
                  请从上方选择一个供应商查看初审详情
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
    <!-- AI初评对话框 -->
    <div v-if="showAiPreliminaryDialog" class="dialog-overlay" @click="closeAiPreliminaryDialog">
      <div class="dialog ai-preliminary-dialog" @click.stop>
        <div class="dialog-header">
          <h3>AI初评结果</h3>
          <button class="close-btn" @click="closeAiPreliminaryDialog">×</button>
        </div>
        <div class="dialog-body">
          <div v-if="aiPreliminaryResult" class="ai-preliminary-result">
            <div class="result-row">
              <div class="result-label">初评结果：</div>
              <div class="result-value">
                <span :class="['result-badge', aiPreliminaryResult.pass === true ? 'result-pass' : aiPreliminaryResult.pass === false ? 'result-fail' : 'result-unknown']">
                  {{ aiPreliminaryResult.pass === true ? '通过' : aiPreliminaryResult.pass === false ? '不通过' : '未知' }}
                </span>
              </div>
            </div>
            <div class="result-row">
              <div class="result-label">原因说明：</div>
              <div class="result-value reason-text">
                {{ aiPreliminaryResult.reason || '无说明' }}
              </div>
            </div>
          </div>
          <div v-else-if="aiPreliminaryContent" class="ai-preliminary-content">
            <pre>{{ aiPreliminaryContent }}</pre>
          </div>
          <div v-else-if="loadingAiPreliminary" class="loading">
            正在加载AI初评结果...
          </div>
          <div v-else class="empty">
            暂无AI初评结果
          </div>
        </div>
        <div class="dialog-footer">
          <button class="secondary-btn" @click="closeAiPreliminaryDialog">关闭</button>
          <button 
            class="primary-btn" 
            @click="applyAiPreliminaryResult"
            :disabled="!aiPreliminaryResult"
          >
            应用
          </button>
        </div>
      </div>
    </div>
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getProjectDetail, getFileContent, uploadProjectDocuments, downloadFile, renameProjectTitle } from '../api/project'
import { getBidRecords, updateBidRecord } from '../api/bid'
import { generateTender, getTenderGenerationList, useTenderGeneration, deleteTenderGeneration, getTenderGenerationStream, getAiPreliminaryReviewStream, aiPreliminaryReviewAllAsync, getAiPreliminaryReviewAllStatus } from '../api/llm'
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
    const selectedBidRecord = ref(null)
    const aiPreliminaryReviewing = ref(false)
    const aiPreliminaryStatus = ref(null)
    const aiPreliminaryStatusTimer = ref(null)
    const manualPreliminaryReason = ref('')
    const manualPreliminaryStatus = ref('null')
    const savingPreliminary = ref(false)
    const refreshingSuppliers = ref(false)
    let supplierRefreshTimer = null
    const tenderDocument = ref('')
    const loadingDocument = ref(false)
    const businessRequirementDocument = ref('')
    const loadingBusinessRequirement = ref(false)
    const procurementRequirementDocument = ref('')
    const loadingProcurementRequirement = ref(false)
    const showAddDialog = ref(false)
    const showBatchImportDialog = ref(false)
    
    // AI初评对话框相关
    const showAiPreliminaryDialog = ref(false)
    const currentAiPreliminaryBidRecord = ref(null)
    const aiPreliminaryContent = ref('')
    const loadingAiPreliminary = ref(false)
    const aiPreliminaryResult = ref(null)
    
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
        if (bidRecords.value.length && !selectedBidRecord.value) {
          selectedBidRecord.value = bidRecords.value[0]
        }
      } catch (err) {
        console.error('Failed to fetch bid records:', err)
        bidRecords.value = []
        selectedBidRecord.value = null
      }
    }

    const hasIdentifyingSuppliers = computed(() => {
      return bidRecords.value.some(
        bid =>
          bid.identity_status === '识别中' ||
          (bid.identity_recognition_model_session && !bid.supplier_id)
      )
    })

    const stopSupplierAutoRefresh = () => {
      if (supplierRefreshTimer) {
        clearInterval(supplierRefreshTimer)
        supplierRefreshTimer = null
      }
    }

    const startSupplierAutoRefresh = () => {
      // 先停止已有的定时器，避免重复
      stopSupplierAutoRefresh()

      if (!hasIdentifyingSuppliers.value) {
        return
      }

      supplierRefreshTimer = setInterval(async () => {
        try {
          await fetchBidRecords()
          // 如果已经没有识别中的供应商了，就停止自动刷新
          if (!hasIdentifyingSuppliers.value) {
            stopSupplierAutoRefresh()
          }
        } catch (e) {
          console.error('Auto refresh suppliers failed:', e)
        }
      }, 5000)
    }

    const handleRefreshSuppliers = async () => {
      if (refreshingSuppliers.value) return
      try {
        refreshingSuppliers.value = true
        await fetchBidRecords()
        // 手动刷新后，根据最新状态重新设置自动刷新
        if (hasIdentifyingSuppliers.value) {
          startSupplierAutoRefresh()
        } else {
          stopSupplierAutoRefresh()
        }
      } catch (e) {
        console.error('Manual refresh suppliers failed:', e)
      } finally {
        refreshingSuppliers.value = false
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

    const handleSelectBidRecord = (bid) => {
      selectedBidRecord.value = bid
      // 切换供应商时，输入框默认填当前理由
      manualPreliminaryReason.value = getPreliminaryReason(bid) || ''
      // 初始化状态：根据人工初审（preliminary_review）设置
      const preliminaryReview = bid.preliminary_review
      if (preliminaryReview && typeof preliminaryReview.pass !== 'undefined') {
        const status = preliminaryReview.pass
        if (status === true) {
          manualPreliminaryStatus.value = 'true'
        } else if (status === false) {
          manualPreliminaryStatus.value = 'false'
        } else {
          manualPreliminaryStatus.value = 'null'
        }
      } else {
        manualPreliminaryStatus.value = 'null'
      }
    }

    const handleSavePreliminary = async () => {
      if (!selectedBidRecord.value) return
      const reason = manualPreliminaryReason.value?.trim() || ''
      const statusValue = manualPreliminaryStatus.value === 'null' ? null : manualPreliminaryStatus.value === 'true'
      
      // 如果状态为"未开始"且理由为空，则保存为 null（清空）
      // 否则保存为 {"pass": true/false, "reason": "..."}
      let preliminaryReviewValue = null
      if (statusValue !== null || reason) {
        preliminaryReviewValue = {
          pass: statusValue,
          reason: reason
        }
      }
      
      try {
        savingPreliminary.value = true
        const bid = selectedBidRecord.value
        // 保存到人工初审（preliminary_review）字段
        await updateBidRecord(bid.project_id, bid.supplier?.id || bid.supplier_id, {
          preliminary_review: preliminaryReviewValue
        })
        // 更新本地数据
        await fetchBidRecords()
        // 重新设置当前选中记录
        const refreshed = bidRecords.value.find(
          (item) => item.bid_record_id === bid.bid_record_id
        )
        if (refreshed) {
          selectedBidRecord.value = refreshed
          manualPreliminaryReason.value = getPreliminaryReason(refreshed) || ''
          const preliminaryReview = refreshed.preliminary_review
          if (preliminaryReview && typeof preliminaryReview.pass !== 'undefined') {
            const status = preliminaryReview.pass
            if (status === true) {
              manualPreliminaryStatus.value = 'true'
            } else if (status === false) {
              manualPreliminaryStatus.value = 'false'
            } else {
              manualPreliminaryStatus.value = 'null'
            }
          } else {
            manualPreliminaryStatus.value = 'null'
          }
        }
        alert('初审结果和理由已更新')
      } catch (err) {
        alert(err.response?.data?.detail || err.message || '更新失败')
      } finally {
        savingPreliminary.value = false
      }
    }

    const getPreliminaryStatusText = (bid) => {
      // 优先显示人工初审结果（preliminary_review.pass）
      const preliminaryReview = bid.preliminary_review
      if (preliminaryReview) {
        // 如果是字符串，尝试解析
        let reviewData = preliminaryReview
        if (typeof preliminaryReview === 'string') {
          try {
            reviewData = JSON.parse(preliminaryReview)
          } catch (e) {
            console.error('解析人工初审JSON失败:', e, preliminaryReview)
            // 解析失败，继续检查AI初审
          }
        }
        
        // 检查 pass 字段
        if (reviewData && (reviewData.pass === true || reviewData.pass === false)) {
          return reviewData.pass === true ? '通过' : '不通过'
        }
      }
      
      // 如果没有人工初审，显示AI初审结果（ai_preliminary_review.pass）
      const aiReview = bid.ai_preliminary_review
      if (aiReview) {
        // 如果是字符串，尝试解析
        let reviewData = aiReview
        if (typeof aiReview === 'string') {
          try {
            reviewData = JSON.parse(aiReview)
          } catch (e) {
            console.error('解析AI初审JSON失败:', e, aiReview)
            return '未开始'
          }
        }
        
        // 检查 pass 字段（支持布尔值和字符串）
        if (reviewData) {
          const passValue = reviewData.pass
          if (passValue === true || passValue === 'true' || passValue === 'True') {
            return '通过'
          } else if (passValue === false || passValue === 'false' || passValue === 'False') {
            return '不通过'
          }
        }
      }
      
      return '未开始'
    }

    const getPreliminaryStatusClass = (bid) => {
      // 优先显示人工初审结果（preliminary_review.pass）
      const preliminaryReview = bid.preliminary_review
      if (preliminaryReview) {
        // 如果是字符串，尝试解析
        let reviewData = preliminaryReview
        if (typeof preliminaryReview === 'string') {
          try {
            reviewData = JSON.parse(preliminaryReview)
          } catch (e) {
            // 解析失败，继续检查AI初审
          }
        }
        
        // 检查 pass 字段
        if (reviewData && (reviewData.pass === true || reviewData.pass === false)) {
          return reviewData.pass === true ? 'status-success' : 'status-failed'
        }
      }
      
      // 如果没有人工初审，显示AI初审结果（ai_preliminary_review.pass）
      const aiReview = bid.ai_preliminary_review
      if (aiReview) {
        // 如果是字符串，尝试解析
        let reviewData = aiReview
        if (typeof aiReview === 'string') {
          try {
            reviewData = JSON.parse(aiReview)
          } catch (e) {
            return 'status-pending'
          }
        }
        
        // 检查 pass 字段（支持布尔值和字符串）
        if (reviewData) {
          const passValue = reviewData.pass
          if (passValue === true || passValue === 'true' || passValue === 'True') {
            return 'status-success'
          } else if (passValue === false || passValue === 'false' || passValue === 'False') {
            return 'status-failed'
          }
        }
      }
      
      return 'status-pending'
    }

    const isPreliminaryFromAI = (bid) => {
      // 判断当前显示的初审结果是否来自AI
      const preliminaryReview = bid.preliminary_review
      if (preliminaryReview) {
        // 如果有人工初审结果，返回false
        let reviewData = preliminaryReview
        if (typeof preliminaryReview === 'string') {
          try {
            reviewData = JSON.parse(preliminaryReview)
          } catch (e) {
            return false
          }
        }
        if (reviewData && typeof reviewData.pass !== 'undefined') {
          return false // 有人工初审，不是AI
        }
      }
      
      // 如果没有人工初审，但有AI初审，返回true
      const aiReview = bid.ai_preliminary_review
      if (aiReview) {
        let reviewData = aiReview
        if (typeof aiReview === 'string') {
          try {
            reviewData = JSON.parse(aiReview)
          } catch (e) {
            return false
          }
        }
        if (reviewData && typeof reviewData.pass !== 'undefined') {
          return true // 是AI初审结果
        }
      }
      
      return false
    }

    const getPreliminaryReason = (bid) => {
      const manual = bid.preliminary_review
      const ai = bid.ai_preliminary_review
      
      const extractReason = (obj) => {
        if (!obj) return ''
        return (
          obj.reason ||
          obj.理由 ||
          obj.comment ||
          obj.说明 ||
          ''
        )
      }
      
      // 优先使用人工初审的理由
      const manualReason = extractReason(manual)
      if (manualReason) {
        return manualReason
      }
      
      // 如果没有人工初审的理由，使用AI初审的理由
      const aiReason = extractReason(ai)
      if (aiReason) {
        return aiReason
      }
      
      if (ai || manual) {
        try {
          return JSON.stringify(manual || ai)
        } catch (e) {
          return '无明确理由'
        }
      }
      
      return ''
    }

    // 判断理由是否来自AI初审（用于显示标识）
    const isReasonFromAI = (bid) => {
      const manual = bid.preliminary_review
      const ai = bid.ai_preliminary_review
      
      // 如果有人工初审的理由，返回false
      const extractReason = (obj) => {
        if (!obj) return ''
        return (
          obj.reason ||
          obj.理由 ||
          obj.comment ||
          obj.说明 ||
          ''
        )
      }
      
      const manualReason = extractReason(manual)
      if (manualReason) {
        return false
      }
      
      // 如果没有人工初审的理由，但有AI初审的理由，返回true
      const aiReason = extractReason(ai)
      if (aiReason) {
        return true
      }
      
      return false
    }

    const handleAiPreliminaryReview = async () => {
      if (!projectId.value) return
      
      try {
        aiPreliminaryReviewing.value = true
        aiPreliminaryStatus.value = null
        
        // 调用异步批量AI初评接口
        // 注意：axios 响应拦截器已经返回了 response.data，所以 response 就是数据本身
        const response = await aiPreliminaryReviewAllAsync(projectId.value)
        
        // 显示启动成功消息
        notification.value = {
          visible: true,
          message: `AI初评任务已启动，共 ${response.pending || 0} 条记录待处理`,
          type: 'success'
        }
        
        // 启动状态轮询
        startStatusPolling()
      } catch (err) {
        console.error('启动AI初评失败:', err)
        notification.value = {
          visible: true,
          message: err.message || '启动AI初评失败',
          type: 'error'
        }
        aiPreliminaryReviewing.value = false
      }
    }

    const startStatusPolling = () => {
      // 清除之前的定时器
      if (aiPreliminaryStatusTimer.value) {
        clearInterval(aiPreliminaryStatusTimer.value)
      }
      
      // 立即查询一次状态
      queryAiPreliminaryStatus()
      
      // 每3秒轮询一次状态
      aiPreliminaryStatusTimer.value = setInterval(() => {
        queryAiPreliminaryStatus()
      }, 3000)
    }

    const stopStatusPolling = () => {
      if (aiPreliminaryStatusTimer.value) {
        clearInterval(aiPreliminaryStatusTimer.value)
        aiPreliminaryStatusTimer.value = null
      }
    }

    const queryAiPreliminaryStatus = async () => {
      if (!projectId.value) return
      
      try {
        // 注意：axios 响应拦截器已经返回了 response.data，所以 response 就是数据本身
        const response = await getAiPreliminaryReviewAllStatus(projectId.value)
        aiPreliminaryStatus.value = response
        
        // 如果所有任务都完成了（没有processing和pending的记录），停止轮询
        if (
          aiPreliminaryStatus.value &&
          aiPreliminaryStatus.value.processing_count === 0 &&
          aiPreliminaryStatus.value.pending_count === 0
        ) {
          stopStatusPolling()
          aiPreliminaryReviewing.value = false
          
          // 刷新投标记录列表
          await fetchBidRecords()
          
          // 显示完成消息
          const successCount = aiPreliminaryStatus.value.success_count || 0
          const failedCount = aiPreliminaryStatus.value.failed_count || 0
          notification.value = {
            visible: true,
            message: `AI初评完成！成功: ${successCount} 条，失败: ${failedCount} 条`,
            type: 'success'
          }
        }
      } catch (err) {
        console.error('查询AI初评状态失败:', err)
        // 查询失败时不显示错误，避免干扰用户
      }
    }

    const handleAiPreliminaryClick = async (bidRecord) => {
      currentAiPreliminaryBidRecord.value = bidRecord
      showAiPreliminaryDialog.value = true
      aiPreliminaryContent.value = ''
      loadingAiPreliminary.value = true
      aiPreliminaryResult.value = null

      try {
        // 先尝试获取流式响应或结果
        const response = await getAiPreliminaryReviewStream(
          bidRecord.project_id,
          bidRecord.supplier_id
        )
        
        const contentType = response.headers.get('content-type')
        
        if (contentType && contentType.includes('application/json')) {
          // 如果是 JSON 响应，说明已经有结果了
          const data = await response.json()
          aiPreliminaryResult.value = data.ai_preliminary_review
          if (aiPreliminaryResult.value) {
            aiPreliminaryContent.value = JSON.stringify(aiPreliminaryResult.value, null, 2)
          }
        } else {
          // 否则是流式响应
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''
          
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))
                  if (data.type === 'chunk' && data.content) {
                    aiPreliminaryContent.value += data.content
                  } else if (data.type === 'status') {
                    // 状态更新
                  } else if (data.type === 'error') {
                    throw new Error(data.error)
                  }
                } catch (e) {
                  console.error('解析SSE数据失败:', e)
                }
              }
            }
          }
          
          // 尝试解析最终内容为 JSON
          try {
            const parsed = JSON.parse(aiPreliminaryContent.value)
            if (parsed.reason && typeof parsed.pass !== 'undefined') {
              aiPreliminaryResult.value = parsed
            }
          } catch (e) {
            // 如果不是 JSON，保持原样显示
          }
        }
      } catch (err) {
        console.error('获取AI初评结果失败:', err)
        aiPreliminaryContent.value = `获取AI初评结果失败: ${err.message}`
      } finally {
        loadingAiPreliminary.value = false
      }
    }

    const closeAiPreliminaryDialog = () => {
      showAiPreliminaryDialog.value = false
      currentAiPreliminaryBidRecord.value = null
      aiPreliminaryContent.value = ''
      aiPreliminaryResult.value = null
    }

    const applyAiPreliminaryResult = async () => {
      if (!aiPreliminaryResult.value || !currentAiPreliminaryBidRecord.value) return
      
      try {
        const bid = currentAiPreliminaryBidRecord.value
        await updateBidRecord(bid.project_id, bid.supplier_id, {
          ai_preliminary_review: aiPreliminaryResult.value,
          ai_preliminary_review_success: aiPreliminaryResult.value.pass
        })
        
        // 刷新列表
        await fetchBidRecords()
        
        // 如果当前选中的是这个记录，更新选中记录
        if (selectedBidRecord.value && selectedBidRecord.value.bid_record_id === bid.bid_record_id) {
          const refreshed = bidRecords.value.find(
            (item) => item.bid_record_id === bid.bid_record_id
          )
          if (refreshed) {
            selectedBidRecord.value = refreshed
            manualPreliminaryReason.value = getPreliminaryReason(refreshed) || ''
            const status = refreshed.ai_preliminary_review_success
            if (status === true) {
              manualPreliminaryStatus.value = 'true'
            } else if (status === false) {
              manualPreliminaryStatus.value = 'false'
            } else {
              manualPreliminaryStatus.value = 'null'
            }
          }
        }
        
        alert('AI初评结果已应用')
        closeAiPreliminaryDialog()
      } catch (err) {
        alert(err.response?.data?.detail || err.message || '应用失败')
      }
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
      // 初始化时，如果有识别中的供应商，则启动自动刷新
      if (hasIdentifyingSuppliers.value) {
        startSupplierAutoRefresh()
      }
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

    // 监听识别中状态的变化，自动控制轮询
    watch(
      hasIdentifyingSuppliers,
      (newVal) => {
        if (newVal) {
          startSupplierAutoRefresh()
        } else {
          stopSupplierAutoRefresh()
        }
      }
    )

    onUnmounted(() => {
      stopSupplierAutoRefresh()
      stopStatusPolling()
    })

    return {
      projectId,
      projectName,
      projectDetail,
      activeTab,
      bidRecords,
      selectedBidRecord,
      aiPreliminaryReviewing,
      manualPreliminaryReason,
      manualPreliminaryStatus,
      savingPreliminary,
      handleSavePreliminary,
      refreshingSuppliers,
      tenderDocument,
      loadingDocument,
      businessRequirementDocument,
      loadingBusinessRequirement,
      procurementRequirementDocument,
      loadingProcurementRequirement,
      showAddDialog,
      showBatchImportDialog,
      handleAddSuccess,
      showAiPreliminaryDialog,
      currentAiPreliminaryBidRecord,
      aiPreliminaryContent,
      loadingAiPreliminary,
      aiPreliminaryResult,
      handleAiPreliminaryClick,
      closeAiPreliminaryDialog,
      applyAiPreliminaryResult,
      handleBatchImportSuccess,
      handleRefreshSuppliers,
      handleSelectBidRecord,
      getPreliminaryStatusText,
      getPreliminaryStatusClass,
      isPreliminaryFromAI,
      getPreliminaryReason,
      isReasonFromAI,
      handleAiPreliminaryReview,
      aiPreliminaryStatus,
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

/* AI初评对话框样式 */
.ai-preliminary-dialog {
  max-width: 800px;
  width: 90%;
}

.ai-preliminary-content {
  max-height: 400px;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
}

.ai-preliminary-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

/* AI初评结果两栏显示样式 */
.ai-preliminary-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.result-label {
  min-width: 100px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  padding-top: 4px;
}

.result-value {
  flex: 1;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
}

.result-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 14px;
}

.result-pass {
  background-color: #d4edda;
  color: #155724;
}

.result-fail {
  background-color: #f8d7da;
  color: #721c24;
}

.result-unknown {
  background-color: #fff3cd;
  color: #856404;
}

.reason-text {
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  white-space: pre-wrap;
  word-wrap: break-word;
  min-height: 60px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
}

.secondary-btn {
  padding: 8px 16px;
  background-color: #fff;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.secondary-btn:hover {
  background-color: #f5f5f5;
  border-color: var(--primary-color);
}

/* 初审 Tab 样式 */
.preliminary-tab {
  height: 100%;
}

.preliminary-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.preliminary-suppliers-grid {
  margin-bottom: 8px;
}

.preliminary-detail {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.preliminary-detail-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.preliminary-detail-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.preliminary-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.preliminary-row .label {
  flex-shrink: 0;
  padding-top: 6px;
  width: 72px;
}

.preliminary-row .value {
  flex: 1;
  text-align: left;
}

.preliminary-status-edit {
  width: 100%;
}

.preliminary-status-edit .status-select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  background-color: #fff;
  cursor: pointer;
}

.preliminary-status-edit .status-select:hover {
  border-color: var(--primary-color);
}

.preliminary-reason-edit {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.preliminary-reason-edit .reason-textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
}

.preliminary-reason-edit .reason-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.preliminary-save-actions {
  display: flex;
  justify-content: flex-end;
}

.preliminary-save-actions .primary-btn {
  padding: 8px 16px;
  background-color: var(--primary-color);
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.preliminary-save-actions .primary-btn:hover:not(:disabled) {
  background-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.preliminary-save-actions .primary-btn:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.6;
}

.preliminary-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.ai-review-btn {
  padding: 8px 16px;
  background-color: var(--primary-color);
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.ai-review-btn:hover:not(:disabled) {
  background-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.ai-review-btn:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.6;
}

.ai-review-status {
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  min-width: 300px;
}

.status-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
}

.status-summary > span {
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #fff;
}

.status-summary .status-success {
  color: var(--success-color);
  background-color: #f0f9ff;
}

.status-summary .status-failed {
  color: var(--danger-color);
  background-color: #fef0f0;
}

.status-summary .status-processing {
  color: var(--warning-color);
  background-color: #fdf6ec;
}

.status-summary .status-pending {
  color: var(--text-secondary);
  background-color: #f5f7fa;
}
</style>
