<template>
  <div class="tool-management">
    <div class="page-header">
      <h1>工具管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="initializeTools" :loading="initializing">
          初始化默认工具
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索工具名称或描述"
        style="width: 300px"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="selectedCategory"
        placeholder="选择分类"
        style="width: 200px; margin-left: 10px"
        clearable
      >
        <el-option label="全部" value="" />
        <el-option label="市场数据" value="market" />
        <el-option label="社交媒体" value="social" />
        <el-option label="新闻分析" value="news" />
        <el-option label="基本面" value="fundamentals" />
        <el-option label="通用" value="general" />
      </el-select>

      <el-switch
        v-model="enabledOnly"
        active-text="仅显示启用"
        style="margin-left: 10px"
      />
    </div>

    <el-table
      :data="filteredTools"
      style="width: 100%"
      v-loading="loading"
      border
      stripe
    >
      <el-table-column prop="tool_id" label="工具ID" width="200" />
      <el-table-column prop="name" label="工具名称" width="200" />
      <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="120">
        <template #default="scope">
          <el-tag :type="getCategoryType(scope.row.category)">
            {{ getCategoryName(scope.row.category) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enabled" label="状态" width="100">
        <template #default="scope">
          <el-switch
            v-model="scope.row.enabled"
            @change="toggleToolStatus(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="remarks" label="备注" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="scope">
          <el-button
            type="success"
            size="small"
            @click="openTestDialog(scope.row)"
            link
          >
            <el-icon><VideoPlay /></el-icon>
            测试
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="editRemarks(scope.row)"
            link
          >
            <el-icon><Edit /></el-icon>
            备注
          </el-button>
          <el-button
            type="info"
            size="small"
            @click="viewDetails(scope.row)"
            link
          >
            <el-icon><View /></el-icon>
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="remarksDialogVisible"
      title="编辑备注"
      width="500px"
    >
      <el-form :model="remarksForm" label-width="80px">
        <el-form-item label="工具名称">
          <el-input v-model="remarksForm.name" disabled />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="remarksForm.remarks"
            type="textarea"
            :rows="4"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="remarksDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRemarks" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailsDialogVisible"
      title="工具详情"
      width="800px"
    >
      <div v-if="selectedTool">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="工具ID">
            {{ selectedTool.tool_id }}
          </el-descriptions-item>
          <el-descriptions-item label="工具名称">
            {{ selectedTool.name }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag :type="getCategoryType(selectedTool.category)">
              {{ getCategoryName(selectedTool.category) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedTool.enabled ? 'success' : 'info'">
              {{ selectedTool.enabled ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedTool.description }}
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            {{ selectedTool.remarks || '无' }}
          </el-descriptions-item>
        </el-descriptions>

        <h3 style="margin-top: 20px;">参数列表</h3>
        <el-table :data="selectedTool.parameters" border size="small">
          <el-table-column prop="name" label="参数名称" width="200" />
          <el-table-column prop="type" label="参数类型" width="200" />
          <el-table-column prop="default" label="默认值" width="150" />
          <el-table-column prop="required" label="是否必填" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.required ? 'danger' : 'success'" size="small">
                {{ scope.row.required ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="detailsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="testDialogVisible"
      :title="`测试工具: ${testForm.toolName}`"
      width="700px"
      destroy-on-close
    >
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="工具ID">
          <el-input :value="testForm.toolId" disabled />
        </el-form-item>

        <el-form-item v-if="testForm.parameters.length > 0" label="参数">
          <div class="params-container">
            <div v-for="param in testForm.parameters" :key="param.name" class="param-item">
              <span class="param-label">{{ param.name }}</span>
              <el-input
                v-model="testForm.paramValues[param.name]"
                :placeholder="`请输入${param.name}${param.default ? '(可选)' : ''}`"
                size="default"
              >
                <template #prefix><span class="param-type">{{ param.type }}</span></template>
              </el-input>
            </div>
          </div>
        </el-form-item>

        <el-form-item v-if="testForm.parameters.length === 0">
          <el-empty description="该工具无需参数" :image-size="60" />
        </el-form-item>

        <el-form-item v-if="testForm.result" label="测试结果">
          <el-input
            v-model="testForm.result"
            type="textarea"
            :rows="10"
            readonly
            class="result-textarea"
          />
        </el-form-item>

        <el-form-item v-if="testForm.error" label="错误信息">
          <el-input
            v-model="testForm.error"
            type="textarea"
            :rows="5"
            readonly
            class="error-textarea"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="runTest"
          :loading="testing"
          :disabled="!testForm.canTest"
        >
          运行测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Edit, View, VideoPlay } from '@element-plus/icons-vue'
import ApiClient from '@/api/request'

const tools = ref([])
const loading = ref(false)
const initializing = ref(false)
const saving = ref(false)
const testing = ref(false)
const searchKeyword = ref('')
const selectedCategory = ref('')
const enabledOnly = ref(false)

const remarksDialogVisible = ref(false)
const detailsDialogVisible = ref(false)
const testDialogVisible = ref(false)
const remarksForm = ref({
  tool_id: '',
  name: '',
  remarks: ''
})
const selectedTool = ref(null)

const testForm = ref({
  toolId: '',
  toolName: '',
  parameters: [],
  paramValues: {},
  result: '',
  error: '',
  canTest: true
})

const filteredTools = computed(() => {
  let result = tools.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(tool =>
      tool.name.toLowerCase().includes(keyword) ||
      tool.description.toLowerCase().includes(keyword)
    )
  }

  if (selectedCategory.value) {
    result = result.filter(tool => tool.category === selectedCategory.value)
  }

  if (enabledOnly.value) {
    result = result.filter(tool => tool.enabled)
  }

  return result
})

const getCategoryName = (category) => {
  const categoryMap = {
    market: '市场数据',
    social: '社交媒体',
    news: '新闻分析',
    fundamentals: '基本面',
    general: '通用'
  }
  return categoryMap[category] || category
}

const getCategoryType = (category) => {
  const typeMap = {
    market: 'primary',
    social: 'success',
    news: 'warning',
    fundamentals: 'danger',
    general: 'info'
  }
  return typeMap[category] || ''
}

const loadTools = async () => {
  loading.value = true
  try {
    const response = await ApiClient.get('/api/tools')
    if (response.success) {
      tools.value = response.data || []
    } else {
      ElMessage.error(response.message || '加载工具列表失败')
    }
  } catch (error) {
    ElMessage.error('加载工具列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const initializeTools = async () => {
  initializing.value = true
  try {
    const response = await ApiClient.post('/api/tools/initialize')
    if (response.success) {
      ElMessage.success('初始化默认工具成功')
      await loadTools()
    } else {
      ElMessage.error(response.message || '初始化默认工具失败')
    }
  } catch (error) {
    ElMessage.error('初始化默认工具失败: ' + error.message)
  } finally {
    initializing.value = false
  }
}

const editRemarks = (tool) => {
  remarksForm.value = {
    tool_id: tool.tool_id,
    name: tool.name,
    remarks: tool.remarks || ''
  }
  remarksDialogVisible.value = true
}

const saveRemarks = async () => {
  saving.value = true
  try {
    const response = await ApiClient.put(`/api/tools/${remarksForm.value.tool_id}`, {
      remarks: remarksForm.value.remarks
    })
    if (response.success) {
      ElMessage.success('保存备注成功')
      remarksDialogVisible.value = false
      await loadTools()
    } else {
      ElMessage.error(response.message || '保存备注失败')
    }
  } catch (error) {
    ElMessage.error('保存备注失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const toggleToolStatus = async (tool) => {
  try {
    const response = await ApiClient.put(`/api/tools/${tool.tool_id}`, {
      enabled: tool.enabled
    })
    if (response.success) {
      ElMessage.success(`${tool.enabled ? '启用' : '禁用'}工具成功`)
    } else {
      tool.enabled = !tool.enabled
      ElMessage.error(response.message || '更新工具状态失败')
    }
  } catch (error) {
    tool.enabled = !tool.enabled
    ElMessage.error('更新工具状态失败: ' + error.message)
  }
}

const viewDetails = (tool) => {
  selectedTool.value = tool
  detailsDialogVisible.value = true
}

const openTestDialog = (tool) => {
  testForm.value = {
    toolId: tool.tool_id,
    toolName: tool.name,
    parameters: tool.parameters || [],
    paramValues: {},
    result: '',
    error: '',
    canTest: true
  }

  for (const param of tool.parameters || []) {
    testForm.value.paramValues[param.name] = param.default || ''
  }

  testDialogVisible.value = true
}

const runTest = async () => {
  const params = {}
  for (const param of testForm.value.parameters) {
    const value = testForm.value.paramValues[param.name]
    if (value !== undefined && value !== '') {
      params[param.name] = value
    }
  }

  testing.value = true
  testForm.value.result = ''
  testForm.value.error = ''

  try {
    const response = await ApiClient.post(`/api/tools/${testForm.value.toolId}/test`, {
      parameters: params
    })

    if (response.success) {
      testForm.value.result = response.result || '执行成功，无返回数据'
      ElMessage.success('工具测试成功')
    } else {
      testForm.value.error = response.error || response.message || '未知错误'
      ElMessage.error('工具测试失败')
    }
  } catch (error) {
    testForm.value.error = error.message || '请求失败'
    ElMessage.error('工具测试失败: ' + error.message)
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadTools()
})
</script>

<style scoped>
.tool-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

h3 {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
}

.params-container {
  width: 100%;
}

.param-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.param-label {
  width: 120px;
  flex-shrink: 0;
  font-size: 14px;
  color: #606266;
}

.param-item .el-input {
  flex: 1;
}

.param-type {
  font-size: 12px;
  color: #909399;
}

.result-textarea,
.error-textarea {
  width: 100%;
}

.result-textarea :deep(.el-textarea__inner),
.error-textarea :deep(.el-textarea__inner) {
  font-family: monospace;
  font-size: 12px;
}
</style>
