<template>
  <div class="workflow-config-container">
    <el-card class="config-header">
      <template #header>
        <div class="card-header">
          <span class="header-title">分析流程配置</span>
          <div class="header-actions">
            <el-button 
              type="primary" 
              @click="initializePresets"
              :loading="loading"
              size="small"
            >
              <el-icon><Refresh /></el-icon>
              初始化预设
            </el-button>
            <el-button 
              type="success" 
              @click="showCreateDialog"
              size="small"
            >
              <el-icon><Plus /></el-icon>
              新建配置
            </el-button>
          </div>
        </div>
      </template>
      <p class="config-description">
        配置股票分析流程参数，包括多空辩论轮次、风险评估轮次、超时时间等。
        分析师团队由股票分析页面选择，此处配置流程参数与不同分析级别关联。
      </p>
    </el-card>

    <el-card class="config-list-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>配置列表</span>
          <el-badge :value="configs.length" type="primary" />
        </div>
      </template>
      
      <el-table :data="configs" style="width: 100%" border>
        <el-table-column prop="name" label="配置名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="关联级别" width="120">
          <template #default="scope">
            <el-tag :type="getLevelType(scope.row.analysis_level)" size="small">
              {{ scope.row.analysis_level }}级
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="辩论轮次" width="100">
          <template #default="scope">
            {{ scope.row.debate_rounds }} 轮
          </template>
        </el-table-column>
        <el-table-column label="风险轮次" width="100">
          <template #default="scope">
            {{ scope.row.risk_discussion_rounds }} 轮
          </template>
        </el-table-column>
        <el-table-column label="情绪/风险" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.enable_sentiment" type="success" size="small">情绪</el-tag>
            <el-tag v-if="scope.row.enable_risk_assessment" type="warning" size="small">风险</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_system" label="类型" width="80">
          <template #default="scope">
            <el-tag v-if="scope.row.is_system" type="info" size="small">系统</el-tag>
            <el-tag v-else type="primary" size="small">自定义</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              @click="editConfig(scope.row)"
              link
              :disabled="scope.row.is_system"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="deleteConfig(scope.row)"
              v-if="!scope.row.is_system"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editingConfig ? '编辑流程配置' : '新建流程配置'"
      width="700px"
      destroy-on-close
    >
      <el-form 
        :model="form" 
        :rules="rules" 
        ref="formRef"
        label-width="140px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input 
            v-model="form.name" 
            placeholder="例如：快速分析、标准分析"
            :disabled="editingConfig?.is_system"
          />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="2"
            placeholder="描述此配置的用途"
          />
        </el-form-item>
        
        <el-form-item label="关联分析级别" prop="analysis_level">
          <el-select 
            v-model="form.analysis_level" 
            placeholder="选择分析级别"
            style="width: 100%"
          >
            <el-option label="1级 - 快速分析" :value="1" />
            <el-option label="2级 - 基础分析" :value="2" />
            <el-option label="3级 - 标准分析" :value="3" />
            <el-option label="4级 - 深度分析" :value="4" />
            <el-option label="5级 - 全面分析" :value="5" />
          </el-select>
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            此配置将关联到选定的分析级别，当用户选择该级别时自动使用
          </div>
        </el-form-item>
        
        <el-divider content-position="left">辩论配置</el-divider>
        
        <el-form-item label="多空辩论轮次" prop="debate_rounds">
          <el-slider 
            v-model="form.debate_rounds" 
            :min="1" 
            :max="3" 
            :marks="debateRoundsMarks"
            :step="1"
            show-stops
          />
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            {{ debateRoundsDescription }}
          </div>
        </el-form-item>
        
        <el-form-item label="每轮超时(秒)" prop="debate_timeout">
          <el-input-number 
            v-model="form.debate_timeout" 
            :min="60" 
            :max="600"
            :step="30"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-divider content-position="left">风险评估配置</el-divider>
        
        <el-form-item label="风险讨论轮次" prop="risk_discussion_rounds">
          <el-slider 
            v-model="form.risk_discussion_rounds" 
            :min="1" 
            :max="3" 
            :marks="riskRoundsMarks"
            :step="1"
            show-stops
          />
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            {{ riskRoundsDescription }}
          </div>
        </el-form-item>
        
        <el-form-item label="风险超时(秒)" prop="risk_timeout">
          <el-input-number 
            v-model="form.risk_timeout" 
            :min="30" 
            :max="300"
            :step="30"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-divider content-position="left">其他配置</el-divider>
        
        <el-form-item label="启用情绪分析">
          <el-switch v-model="form.enable_sentiment" />
        </el-form-item>
        
        <el-form-item label="启用风险评估">
          <el-switch v-model="form.enable_risk_assessment" />
        </el-form-item>
        
        <el-form-item label="最大重试次数" prop="max_retries">
          <el-input-number 
            v-model="form.max_retries" 
            :min="1" 
            :max="5"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="saveConfig" 
            :loading="saving"
          >
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ApiClient } from '@/api/request'

interface WorkflowConfig {
  _id?: string
  name: string
  description?: string
  analysis_level: number
  debate_rounds: number
  debate_timeout: number
  risk_discussion_rounds: number
  risk_timeout: number
  enable_sentiment: boolean
  enable_risk_assessment: boolean
  max_retries: number
  is_system: boolean
  created_at?: string
  updated_at?: string
}

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const configs = ref<WorkflowConfig[]>([])
const editingConfig = ref<WorkflowConfig | null>(null)

const form = reactive({
  name: '',
  description: '',
  analysis_level: 5,
  debate_rounds: 1,
  debate_timeout: 300,
  risk_discussion_rounds: 1,
  risk_timeout: 120,
  enable_sentiment: true,
  enable_risk_assessment: true,
  max_retries: 3
})

const formRef = ref()

const rules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' }
  ],
  analysis_level: [
    { required: true, message: '请选择分析级别', trigger: 'change' }
  ],
  debate_rounds: [
    { required: true, message: '请选择辩论轮次', trigger: 'change' }
  ],
  risk_discussion_rounds: [
    { required: true, message: '请选择风险讨论轮次', trigger: 'change' }
  ]
}

const debateRoundsMarks = {
  1: '1轮（快速）',
  2: '2轮（标准）',
  3: '3轮（深度）'
}

const riskRoundsMarks = {
  1: '1轮（基础）',
  2: '2轮（标准）',
  3: '3轮（深度）'
}

const debateRoundsDescription = computed(() => {
  switch (form.debate_rounds) {
    case 1:
      return '快速辩论：1轮，适合快速分析'
    case 2:
      return '标准辩论：2轮，平衡速度和深度'
    case 3:
      return '深度辩论：3轮，全面深入分析'
    default:
      return '自定义辩论轮次'
  }
})

const riskRoundsDescription = computed(() => {
  switch (form.risk_discussion_rounds) {
    case 1:
      return '基础评估：1轮，快速风险评估'
    case 2:
      return '标准评估：2轮，平衡风险评估'
    case 3:
      return '深度评估：3轮，全面风险评估'
    default:
      return '自定义风险轮次'
  }
})

const getLevelType = (level: number) => {
  const types: Record<number, string> = {
    1: 'info',
    2: '',
    3: 'success',
    4: 'warning',
    5: 'danger'
  }
  return types[level] || ''
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await ApiClient.get('/api/analysis-workflow/workflows')
    if (response.success) {
      configs.value = Array.isArray(response.data) ? response.data : []
    } else {
      ElMessage.error(response.message || '配置加载失败')
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('配置加载失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const initializePresets = async () => {
  loading.value = true
  try {
    const response = await ApiClient.post('/api/analysis-workflow/workflows/initialize-presets')
    if (response.success) {
      ElMessage.success('预设初始化成功')
      await loadConfigs()
    } else {
      ElMessage.error(response.message || '初始化失败')
    }
  } catch (error) {
    console.error('初始化预设失败:', error)
    ElMessage.error('初始化失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  editingConfig.value = null
  Object.assign(form, {
    name: '',
    description: '',
    analysis_level: 5,
    debate_rounds: 1,
    debate_timeout: 300,
    risk_discussion_rounds: 1,
    risk_timeout: 120,
    enable_sentiment: true,
    enable_risk_assessment: true,
    max_retries: 3
  })
  dialogVisible.value = true
}

const editConfig = (config: WorkflowConfig) => {
  editingConfig.value = config
  Object.assign(form, {
    name: config.name,
    description: config.description || '',
    analysis_level: config.analysis_level,
    debate_rounds: config.debate_rounds,
    debate_timeout: config.debate_timeout,
    risk_discussion_rounds: config.risk_discussion_rounds,
    risk_timeout: config.risk_timeout,
    enable_sentiment: config.enable_sentiment,
    enable_risk_assessment: config.enable_risk_assessment,
    max_retries: config.max_retries
  })
  dialogVisible.value = true
}

const saveConfig = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      saving.value = true
      try {
        const configData = {
          name: form.name,
          description: form.description,
          analysis_level: form.analysis_level,
          debate_rounds: form.debate_rounds,
          debate_timeout: form.debate_timeout,
          risk_discussion_rounds: form.risk_discussion_rounds,
          risk_timeout: form.risk_timeout,
          enable_sentiment: form.enable_sentiment,
          enable_risk_assessment: form.enable_risk_assessment,
          max_retries: form.max_retries
        }
        
        let response
        if (editingConfig.value) {
          response = await ApiClient.put(`/api/analysis-workflow/workflows/${editingConfig.value._id}`, configData)
        } else {
          response = await ApiClient.post('/api/analysis-workflow/workflows', configData)
        }
        
        if (response.success) {
          ElMessage.success('配置保存成功')
          dialogVisible.value = false
          await loadConfigs()
        } else {
          ElMessage.error(response.message || '保存失败')
        }
      } catch (error) {
        console.error('保存配置失败:', error)
        ElMessage.error('保存失败，请检查网络连接')
      } finally {
        saving.value = false
      }
    }
  })
}

const deleteConfig = async (config: WorkflowConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置"${config.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await ApiClient.delete(`/api/analysis-workflow/workflows/${config._id}`)
    if (response.success) {
      ElMessage.success('配置删除成功')
      await loadConfigs()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      ElMessage.error('删除失败，请检查网络连接')
    }
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.workflow-config-container {
  padding: 20px;
}

.config-header {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 18px;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.config-description {
  margin-top: 10px;
  color: #606266;
  line-height: 1.5;
}

.config-list-card {
  margin-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.el-slider__marks-text) {
  font-size: 12px;
}

:deep(.el-divider__text) {
  font-weight: 500;
}
</style>
