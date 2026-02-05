<template>
  <div class="agent-config-container">
    <el-card class="config-header">
      <template #header>
        <div class="card-header">
          <span class="header-title">Agent配置管理</span>
          <el-button 
            type="primary" 
            @click="initializeDefaultConfigs"
            :loading="loading"
          >
            <el-icon><Refresh /></el-icon>
            初始化默认配置
          </el-button>
        </div>
      </template>
      <p class="config-description">
        管理所有分析师Agent的配置，包括提示词、工具和其他设置。
        您可以在此页面修改每个Agent的prompt，系统会自动保存到MongoDB中。
      </p>
    </el-card>

    <el-card class="config-list-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>Agent配置列表</span>
          <el-badge :value="Array.isArray(configs) ? configs.length : 0" type="primary" />
        </div>
      </template>
      
      <el-table :data="configs" style="width: 100%" border>
        <el-table-column prop="agent_id" label="Agent ID" width="150">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.agent_id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="scope">
            <el-switch 
              v-model="scope.row.enabled" 
              active-color="#13ce66" 
              inactive-color="#ff4d4f"
              @change="handleStatusChange(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              @click="editConfig(scope.row)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingConfig ? '编辑Agent配置' : '创建Agent配置'"
      width="80%"
      destroy-on-close
    >
      <el-form 
        :model="form" 
        :rules="rules" 
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="Agent ID" prop="agent_id" :disabled="!!editingConfig">
          <el-input v-model="form.agent_id" placeholder="例如：fundamentals, market, news" />
        </el-form-item>
        
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：基本面分析师" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3" 
            placeholder="描述此Agent的功能和职责"
          />
        </el-form-item>
        
        <el-form-item label="系统消息" prop="system_message">
          <el-input 
            v-model="form.system_message" 
            type="textarea" 
            :rows="8" 
            placeholder="Agent的系统提示消息"
          />
        </el-form-item>
        
        <el-form-item label="提示模板" prop="prompt_template">
          <el-input 
            v-model="form.prompt_template" 
            type="textarea" 
            :rows="8" 
            placeholder="Agent的提示模板"
          />
        </el-form-item>
        
        <el-form-item label="工具">
          <el-select
            v-model="form.tools"
            multiple
            filterable
            placeholder="请选择工具"
            style="width: 100%"
          >
            <el-option
              v-for="tool in allTools"
              :key="tool.tool_id"
              :label="`${tool.name} - ${tool.description}`"
              :value="tool.tool_id"
            >
              <div style="display: flex; justify-content: space-between;">
                <span>{{ tool.name }}</span>
                <el-tag size="small" :type="getCategoryType(tool.category)">
                  {{ getCategoryName(tool.category) }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="form.enabled" active-color="#13ce66" inactive-color="#ff4d4f" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Edit } from '@element-plus/icons-vue'
import { ApiClient } from '@/api/request'

// 类型定义
interface AgentConfig {
  agent_id: string
  name: string
  description: string
  system_message: string
  prompt_template: string
  tools: string[]
  enabled: boolean
  version: number
  created_at?: string
  updated_at?: string
}

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const configs = ref<AgentConfig[]>([])
const editingConfig = ref<AgentConfig | null>(null)
const allTools = ref<any[]>([])

// 表单数据
const form = reactive({
  agent_id: '',
  name: '',
  description: '',
  system_message: '',
  prompt_template: '',
  tools: [],
  enabled: true
})

// 表单验证规则
const rules = {
  agent_id: [
    { required: true, message: '请输入Agent ID', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ],
  system_message: [
    { required: true, message: '请输入系统消息', trigger: 'blur' }
  ],
  prompt_template: [
    { required: true, message: '请输入提示模板', trigger: 'blur' }
  ]
}

const formRef = ref()

// 工具分类映射
const getCategoryName = (category: string) => {
  const categoryMap: Record<string, string> = {
    market: '市场数据',
    social: '社交媒体',
    news: '新闻分析',
    fundamentals: '基本面',
    general: '通用'
  }
  return categoryMap[category] || category
}

const getCategoryType = (category: string) => {
  const typeMap: Record<string, string> = {
    market: 'primary',
    social: 'success',
    news: 'warning',
    fundamentals: 'danger',
    general: 'info'
  }
  return typeMap[category] || ''
}

// 方法
const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await ApiClient.get('/api/agent-config')
    if (response.success) {
      configs.value = Array.isArray(response.data) ? response.data : []
      ElMessage.success('配置加载成功')
    } else {
      ElMessage.error(response.message || '配置加载失败')
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const loadAllTools = async () => {
  try {
    const response = await ApiClient.get('/api/tools')
    if (response.success) {
      allTools.value = response.data || []
    } else {
      ElMessage.error(response.message || '加载工具列表失败')
    }
  } catch (error) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载工具列表失败，请检查网络连接')
  }
}

const initializeDefaultConfigs = async () => {
  loading.value = true
  try {
    const response = await ApiClient.post('/api/agent-config/initialize')
    if (response.success) {
      configs.value = Array.isArray(response.data) ? response.data : []
      ElMessage.success('默认配置初始化成功')
    } else {
      ElMessage.error(response.message || '初始化失败')
    }
  } catch (error) {
    console.error('初始化默认配置失败:', error)
    ElMessage.error('初始化失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const editConfig = (config: AgentConfig) => {
  editingConfig.value = config
  Object.assign(form, {
    agent_id: config.agent_id,
    name: config.name,
    description: config.description,
    system_message: config.system_message,
    prompt_template: config.prompt_template,
    tools: [...config.tools],
    enabled: config.enabled
  })
  dialogVisible.value = true
}

const saveConfig = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      saving.value = true
      try {
        const response = await ApiClient.post(`/api/agent-config/${form.agent_id}`, form)
        if (response.success) {
          // 更新本地配置列表
          const index = configs.value.findIndex(c => c.agent_id === form.agent_id)
          if (index !== -1) {
            configs.value[index] = response.data
          } else {
            configs.value.push(response.data)
          }
          ElMessage.success('配置保存成功')
          dialogVisible.value = false
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

const handleStatusChange = async (config: AgentConfig) => {
  try {
    const response = await ApiClient.post(`/api/agent-config/${config.agent_id}`, {
      enabled: config.enabled
    })
    if (response.success) {
      ElMessage.success('状态更新成功')
    } else {
      // 恢复原状态
      config.enabled = !config.enabled
      ElMessage.error(response.message || '状态更新失败')
    }
  } catch (error) {
    // 恢复原状态
    config.enabled = !config.enabled
    console.error('更新状态失败:', error)
    ElMessage.error('状态更新失败，请检查网络连接')
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadConfigs()
  loadAllTools()
})
</script>

<style scoped>
.agent-config-container {
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
  gap: 10px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .agent-config-container {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .el-dialog {
    width: 95% !important;
  }
}
</style>
