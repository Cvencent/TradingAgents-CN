<template>
  <el-dialog
    v-model="dialogVisible"
    title="模型选择预设"
    width="900px"
    destroy-on-close
  >
    <div class="preset-management">
      <!-- 预设列表 -->
      <div class="preset-list">
        <el-empty v-if="presets.length === 0" description="暂无预设" />
        
        <el-card
          v-for="preset in presets"
          :key="preset.id"
          class="preset-card"
          :class="{ 'is-system': preset.is_system, 'is-active': preset.id === activePresetId }"
          shadow="hover"
        >
          <div class="preset-header">
            <div class="preset-title">
              <h4>{{ preset.name }}</h4>
              <el-tag v-if="preset.is_system" type="info" size="small">系统</el-tag>
              <el-tag v-else type="success" size="small">自定义</el-tag>
            </div>
            <el-switch
              v-if="!preset.is_system"
              v-model="preset.is_active"
              @change="(val: boolean) => handleActiveChange(preset.id!, val)"
              inline-prompt
              active-text="启用"
              inactive-text="禁用"
            />
          </div>
          
          <p class="preset-description">{{ preset.description || '暂无描述' }}</p>
          
          <!-- 角色配置预览 -->
          <div class="preset-roles">
            <el-tag
              v-for="(config, roleId) in preset.role_configs"
              :key="roleId"
              size="small"
              effect="plain"
              class="role-tag"
            >
              {{ getRoleName(roleId) }}: {{ config.model_name }}
            </el-tag>
            <el-tag
              v-if="Object.keys(preset.role_configs).length === 0"
              size="small"
              type="info"
              effect="plain"
            >
              使用默认配置
            </el-tag>
          </div>
          
          <div class="preset-actions">
            <el-button
              type="primary"
              size="small"
              @click="handleApply(preset)"
              :loading="applyingId === preset.id"
            >
              应用
            </el-button>
            <el-button
              v-if="!preset.is_system"
              size="small"
              @click="handleEdit(preset)"
            >
              编辑
            </el-button>
            <el-button
              v-if="!preset.is_system"
              type="danger"
              size="small"
              @click="handleDelete(preset)"
            >
              删除
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建新预设
        </el-button>
      </div>
    </template>

    <!-- 创建/编辑预设对话框 -->
    <PresetEditDialog
      v-model="editDialogVisible"
      :preset="editingPreset"
      :providers="providers"
      @save="handleSavePreset"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type {
  ModelSelectionPreset,
  RoleInfo
} from '@/types/roleModelConfig'
import { ALL_ROLES } from '@/types/roleModelConfig'
import { getAllPresets, applyPreset, deletePreset, updatePreset } from '@/api/roleModelConfig'
import PresetEditDialog from './PresetEditDialog.vue'

interface Props {
  modelValue: boolean
  providers: Array<{
    name: string
    display_name: string
    models?: Array<{
      name: string
      display_name?: string
    }>
  }>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'apply': [preset: ModelSelectionPreset]
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 状态
const presets = ref<ModelSelectionPreset[]>([])
const loading = ref(false)
const applyingId = ref<string | null>(null)
const activePresetId = ref<string | null>(null)
const editDialogVisible = ref(false)
const editingPreset = ref<ModelSelectionPreset | null>(null)

// 获取角色名称
const getRoleName = (roleId: string): string => {
  const role = ALL_ROLES.find(r => r.id === roleId)
  return role?.name || roleId
}

// 加载预设列表
const loadPresets = async () => {
  loading.value = true
  try {
    const res = await getAllPresets()
    if (res.success) {
      presets.value = res.data || []
    }
  } catch (error) {
    ElMessage.error('加载预设失败')
  } finally {
    loading.value = false
  }
}

// 应用预设
const handleApply = async (preset: ModelSelectionPreset) => {
  if (!preset.id) return
  
  applyingId.value = preset.id
  try {
    const res = await applyPreset(preset.id)
    if (res.success) {
      ElMessage.success(`预设 "${preset.name}" 已应用`)
      activePresetId.value = preset.id
      emit('apply', preset)
    } else {
      ElMessage.error(res.message || '应用预设失败')
    }
  } catch (error) {
    ElMessage.error('应用预设失败')
  } finally {
    applyingId.value = null
  }
}

// 创建预设
const handleCreate = () => {
  editingPreset.value = null
  editDialogVisible.value = true
}

// 编辑预设
const handleEdit = (preset: ModelSelectionPreset) => {
  editingPreset.value = { ...preset }
  editDialogVisible.value = true
}

// 删除预设
const handleDelete = async (preset: ModelSelectionPreset) => {
  if (!preset.id) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除预设 "${preset.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deletePreset(preset.id)
    if (res.success) {
      ElMessage.success('删除成功')
      await loadPresets()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 保存预设
const handleSavePreset = async (preset: ModelSelectionPreset) => {
  await loadPresets()
}

// 切换预设激活状态
const handleActiveChange = async (presetId: string, isActive: boolean) => {
  try {
    const res = await updatePreset(presetId, { is_active: isActive })
    if (res.success) {
      ElMessage.success(isActive ? '预设已启用' : '预设已禁用')
    } else {
      ElMessage.error(res.message || '操作失败')
      await loadPresets() // 刷新状态
    }
  } catch (error) {
    ElMessage.error('操作失败')
    await loadPresets()
  }
}

// 监听对话框打开
watch(dialogVisible, (val) => {
  if (val) {
    loadPresets()
  }
})
</script>

<style scoped lang="scss">
.preset-management {
  max-height: 60vh;
  overflow-y: auto;
}

.preset-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preset-card {
  transition: all 0.3s ease;

  &.is-system {
    border-left: 4px solid var(--el-color-info);
  }

  &.is-active {
    border-left: 4px solid var(--el-color-success);
    background-color: var(--el-color-success-light-9);
  }

  :deep(.el-card__body) {
    padding: 16px;
  }
}

.preset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .preset-title {
    display: flex;
    align-items: center;
    gap: 8px;

    h4 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }
}

.preset-description {
  margin: 8px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.preset-roles {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0;

  .role-tag {
    font-size: 12px;
  }
}

.preset-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-light);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
