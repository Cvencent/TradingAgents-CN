<template>
  <div class="role-model-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>角色模型配置</h2>
        <p class="subtitle">为每个分析师和角色配置不同的模型参数</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleReset">
          <el-icon><RefreshRight /></el-icon>
          重置
        </el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          <el-icon><Check /></el-icon>
          保存配置
        </el-button>
      </div>
    </div>

    <!-- 快速预设按钮 -->
    <div class="quick-presets">
      <span class="presets-label">快速预设：</span>
      <el-button-group>
        <el-button
          v-for="preset in quickPresets"
          :key="preset.id"
          size="small"
          @click="handleQuickPreset(preset)"
        >
          {{ preset.name }}
        </el-button>
      </el-button-group>
      <el-button
        size="small"
        type="primary"
        plain
        @click="showPresetManagement = true"
      >
        <el-icon><Setting /></el-icon>
        管理预设
      </el-button>
    </div>

    <!-- 主体内容 -->
    <div class="main-content">
      <!-- 左侧角色分类菜单 -->
      <div class="role-category-menu">
        <el-menu
          :default-active="activeCategory"
          @select="handleCategorySelect"
        >
          <el-menu-item index="analysts">
            <el-icon><TrendCharts /></el-icon>
            <span>分析师 ({{ roleConfigs.analysts?.length || 0 }})</span>
          </el-menu-item>
          <el-menu-item index="debaters">
            <el-icon><ChatDotRound /></el-icon>
            <span>辩论者 ({{ roleConfigs.debaters?.length || 0 }})</span>
          </el-menu-item>
          <el-menu-item index="decision_makers">
            <el-icon><User /></el-icon>
            <span>决策者 ({{ roleConfigs.decision_makers?.length || 0 }})</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧配置区域 -->
      <div class="config-area">
        <el-scrollbar>
          <div class="config-list">
            <RoleModelConfigCard
              v-for="roleData in currentCategoryRoles"
              :key="roleData.role_id"
              :ref="(el) => setCardRef(roleData.role_id, el)"
              :role-info="{
                id: roleData.role_id,
                name: roleData.role_name,
                type: roleData.role_type,
                icon: roleData.icon,
                description: roleData.description
              }"
              :config="roleData.current_config"
              :providers="providers"
              @update="handleConfigUpdate"
              @enabled-change="handleEnabledChange"
            />
          </div>
        </el-scrollbar>
      </div>
    </div>

    <!-- 预设管理对话框 -->
    <PresetManagementDialog
      v-model="showPresetManagement"
      :providers="providers"
      @apply="handlePresetApplied"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts,
  ChatDotRound,
  User,
  RefreshRight,
  Check,
  Setting
} from '@element-plus/icons-vue'
import type {
  RoleConfigResponse,
  RoleModelConfigUpdate,
  ModelSelectionPreset,
  RoleConfigsResponse
} from '@/types/roleModelConfig'
import { getAllRoleConfigs, batchUpdateRoleConfigs } from '@/api/roleModelConfig'
import { configApi } from '@/api/config'
import RoleModelConfigCard from './components/RoleModelConfigCard.vue'
import PresetManagementDialog from './components/PresetManagementDialog.vue'

// 组件引用
const cardRefs = ref<Record<string, any>>({})

const setCardRef = (roleId: string, el: any) => {
  if (el) {
    cardRefs.value[roleId] = el
  }
}

// 状态
const loading = ref(false)
const saving = ref(false)
const activeCategory = ref('analysts')
const showPresetManagement = ref(false)

// 数据
const roleConfigs = ref<RoleConfigsResponse>({
  analysts: [],
  debaters: [],
  decision_makers: []
})

const providers = ref<Array<{
  name: string
  display_name: string
  models?: Array<{
    name: string
    display_name?: string
  }>
}>>([])

// 快速预设
const quickPresets = ref([
  { id: 'economy', name: '经济型' },
  { id: 'balanced', name: '平衡型' },
  { id: 'performance', name: '高性能' }
])

// 当前分类的角色
const currentCategoryRoles = computed(() => {
  return roleConfigs.value[activeCategory.value as keyof RoleConfigsResponse] || []
})

// 加载角色配置
const loadRoleConfigs = async () => {
  loading.value = true
  try {
    const res = await getAllRoleConfigs()
    if (res.success) {
      roleConfigs.value = res.data || {
        analysts: [],
        debaters: [],
        decision_makers: []
      }
    } else {
      ElMessage.error(res.message || '加载配置失败')
    }
  } catch (error) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 加载厂家列表
const loadProviders = async () => {
  try {
    const res = await configApi.getLLMProviders()
    if (res) {
      providers.value = res || []
    }
  } catch (error) {
    console.error('加载厂家列表失败:', error)
  }
}

// 处理分类选择
const handleCategorySelect = (index: string) => {
  activeCategory.value = index
}

// 处理配置更新
const handleConfigUpdate = (roleId: string, config: RoleModelConfigUpdate) => {
  // 配置卡片内部已处理，这里可以添加额外的逻辑
  console.log('配置更新:', roleId, config)
}

// 处理启用状态变化
const handleEnabledChange = (roleId: string, enabled: boolean) => {
  console.log('启用状态变化:', roleId, enabled)
}

// 保存配置
const handleSave = async () => {
  // 收集所有卡片的配置
  const configs: Array<RoleModelConfigUpdate & { role_id: string; is_enabled: boolean }> = []
  
  for (const [roleId, cardRef] of Object.entries(cardRefs.value)) {
    if (cardRef && cardRef.getConfig) {
      const config = cardRef.getConfig()
      if (config) {
        configs.push(config)
      }
    }
  }
  
  if (configs.length === 0) {
    ElMessage.warning('没有可保存的配置')
    return
  }
  
  saving.value = true
  try {
    const res = await batchUpdateRoleConfigs(configs)
    if (res.success) {
      const { success: successList, failed } = res.data || { success: [], failed: [] }
      if (failed.length === 0) {
        ElMessage.success(`成功保存 ${successList.length} 个角色配置`)
      } else {
        ElMessage.warning(`保存完成: 成功 ${successList.length}, 失败 ${failed.length}`)
        console.error('失败的配置:', failed)
      }
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 重置配置
const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有配置吗？这将重新加载服务器上的配置。',
      '确认重置',
      {
        confirmButtonText: '重置',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await loadRoleConfigs()
    ElMessage.success('配置已重置')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

// 快速预设
const handleQuickPreset = async (preset: { id: string; name: string }) => {
  try {
    await ElMessageBox.confirm(
      `确定要应用 "${preset.name}" 预设吗？这将覆盖当前的模型配置。`,
      '确认应用预设',
      {
        confirmButtonText: '应用',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    // TODO: 实现快速预设逻辑
    ElMessage.info(`正在应用 "${preset.name}" 预设...`)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('应用预设失败:', error)
    }
  }
}

// 预设应用后的处理
const handlePresetApplied = (preset: ModelSelectionPreset) => {
  // 重新加载配置
  loadRoleConfigs()
  ElMessage.success(`预设 "${preset.name}" 已应用`)
}

// 初始化
onMounted(() => {
  loadRoleConfigs()
  loadProviders()
})
</script>

<style scoped lang="scss">
.role-model-config-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  background-color: var(--el-bg-color-page);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;

  .header-left {
    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .subtitle {
      margin: 0;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.quick-presets {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background-color: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);

  .presets-label {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    font-weight: 500;
  }
}

.main-content {
  display: flex;
  flex: 1;
  gap: 20px;
  overflow: hidden;
  background-color: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.role-category-menu {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--el-border-color-light);
  background-color: var(--el-bg-color);

  :deep(.el-menu) {
    border-right: none;
  }
}

.config-area {
  flex: 1;
  overflow: hidden;
  padding: 20px;

  .config-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}
</style>
