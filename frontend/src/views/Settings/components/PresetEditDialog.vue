<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑预设' : '创建预设'"
    width="800px"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <!-- 基本信息 -->
      <el-form-item label="预设名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="输入预设名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="预设描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="可选：输入预设描述"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-divider>角色配置</el-divider>

      <!-- 角色配置表格 -->
      <div class="role-configs-section">
        <el-table
          :data="roleConfigsList"
          style="width: 100%"
          size="small"
          border
        >
          <el-table-column prop="roleName" label="角色" width="140" />
          <el-table-column prop="roleType" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="getRoleTypeTag(row.roleType)">
                {{ getRoleTypeName(row.roleType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="厂家" width="140">
            <template #default="{ row }">
              <el-select
                v-model="row.config.provider"
                placeholder="选择厂家"
                filterable
                size="small"
                @change="() => handleProviderChange(row)"
              >
                <el-option
                  v-for="provider in providers"
                  :key="provider.name"
                  :label="provider.display_name"
                  :value="provider.name"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="模型" min-width="140">
            <template #default="{ row }">
              <el-select
                v-model="row.config.model_name"
                placeholder="选择模型"
                filterable
                allow-create
                default-first-option
                reserve-keyword
                size="small"
                :disabled="!row.config.provider"
              >
                <el-option
                  v-for="model in getAvailableModels(row.config.provider)"
                  :key="model.name"
                  :label="model.display_name || model.name"
                  :value="model.name"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="温度" width="100">
            <template #default="{ row }">
              <el-input-number
                v-model="row.config.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                size="small"
                style="width: 80px"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                type="danger"
                link
                size="small"
                @click="handleClearRoleConfig(row)"
              >
                清除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-divider>默认配置</el-divider>

      <!-- 默认配置 -->
      <el-form-item label="默认厂家" prop="default_provider">
        <el-select
          v-model="formData.default_provider"
          placeholder="选择默认厂家"
          filterable
          style="width: 100%"
          @change="handleDefaultProviderChange"
        >
          <el-option
            v-for="provider in providers"
            :key="provider.name"
            :label="provider.display_name"
            :value="provider.name"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="默认模型" prop="default_model">
        <el-select
          v-model="formData.default_model"
          placeholder="选择默认模型"
          filterable
          allow-create
          default-first-option
          reserve-keyword
          style="width: 100%"
          :disabled="!formData.default_provider"
        >
          <el-option
            v-for="model in defaultAvailableModels"
            :key="model.name"
            :label="model.display_name || model.name"
            :value="model.name"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type {
  ModelSelectionPreset,
  ModelSelectionPresetCreate,
  RoleModelConfigRef,
  RoleType
} from '@/types/roleModelConfig'
import {
  ALL_ROLES,
  ROLE_TYPE_NAMES,
  ANALYST_ROLES,
  DEBATER_ROLES,
  DECISION_ROLES
} from '@/types/roleModelConfig'
import { createPreset, updatePreset } from '@/api/roleModelConfig'

interface Props {
  modelValue: boolean
  preset: ModelSelectionPreset | null
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
  'save': [preset: ModelSelectionPreset]
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.preset?.id)

// 表单引用
const formRef = ref<FormInstance>()
const saving = ref(false)

// 表单数据
const formData = ref<ModelSelectionPresetCreate>({
  name: '',
  description: '',
  role_configs: {},
  default_provider: '',
  default_model: ''
})

// 角色配置列表（用于表格显示）
const roleConfigsList = ref<Array<{
  roleId: string
  roleName: string
  roleType: RoleType
  config: RoleModelConfigRef
}>>([])

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入预设名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  default_provider: [
    { required: true, message: '请选择默认厂家', trigger: 'change' }
  ],
  default_model: [
    { required: true, message: '请选择默认模型', trigger: 'change' }
  ]
}

// 计算默认配置可用的模型
const defaultAvailableModels = computed(() => {
  if (!formData.value.default_provider) return []
  const provider = props.providers.find(p => p.name === formData.value.default_provider)
  return provider?.models || []
})

// 获取角色类型标签样式
const getRoleTypeTag = (type: RoleType): string => {
  const tagMap: Record<RoleType, string> = {
    analyst: 'primary',
    debater: 'warning',
    decision_maker: 'success'
  }
  return tagMap[type] || 'info'
}

// 获取角色类型名称
const getRoleTypeName = (type: RoleType): string => {
  return ROLE_TYPE_NAMES[type] || type
}

// 获取可用模型列表
const getAvailableModels = (providerName: string) => {
  if (!providerName) return []
  const provider = props.providers.find(p => p.name === providerName)
  return provider?.models || []
}

// 处理厂家变化
const handleProviderChange = (row: any) => {
  row.config.model_name = ''
}

// 处理默认厂家变化
const handleDefaultProviderChange = () => {
  formData.value.default_model = ''
}

// 清除角色配置
const handleClearRoleConfig = (row: any) => {
  row.config = {
    provider: '',
    model_name: '',
    temperature: 0.7,
    max_tokens: 4000
  }
}

// 初始化角色配置列表
const initRoleConfigsList = () => {
  roleConfigsList.value = ALL_ROLES.map(role => {
    const existingConfig = formData.value.role_configs[role.id]
    return {
      roleId: role.id,
      roleName: role.name,
      roleType: role.type,
      config: existingConfig || {
        provider: '',
        model_name: '',
        temperature: 0.7,
        max_tokens: 4000
      }
    }
  })
}

// 从角色配置列表更新表单数据
const updateFormRoleConfigs = () => {
  formData.value.role_configs = {}
  roleConfigsList.value.forEach(item => {
    if (item.config.provider && item.config.model_name) {
      formData.value.role_configs[item.roleId] = {
        provider: item.config.provider,
        model_name: item.config.model_name,
        temperature: item.config.temperature,
        max_tokens: item.config.max_tokens
      }
    }
  })
}

// 保存预设
const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    // 更新角色配置
    updateFormRoleConfigs()
    
    saving.value = true
    
    if (isEdit.value && props.preset?.id) {
      // 更新现有预设
      const res = await updatePreset(props.preset.id, {
        name: formData.value.name,
        description: formData.value.description,
        role_configs: formData.value.role_configs,
        default_provider: formData.value.default_provider,
        default_model: formData.value.default_model
      })
      
      if (res.success) {
        ElMessage.success('预设更新成功')
        emit('save', res.data)
        dialogVisible.value = false
      } else {
        ElMessage.error(res.message || '更新失败')
      }
    } else {
      // 创建新预设
      const res = await createPreset(formData.value)
      
      if (res.success) {
        ElMessage.success('预设创建成功')
        emit('save', res.data)
        dialogVisible.value = false
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    }
  } catch (error: any) {
    if (error !== 'validation') {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    saving.value = false
  }
}

// 监听对话框打开和预设变化
watch(() => props.modelValue, (val) => {
  if (val) {
    if (props.preset) {
      // 编辑模式
      formData.value = {
        name: props.preset.name,
        description: props.preset.description || '',
        role_configs: { ...props.preset.role_configs },
        default_provider: props.preset.default_provider,
        default_model: props.preset.default_model
      }
    } else {
      // 创建模式
      formData.value = {
        name: '',
        description: '',
        role_configs: {},
        default_provider: '',
        default_model: ''
      }
    }
    initRoleConfigsList()
  }
})
</script>

<style scoped lang="scss">
.role-configs-section {
  margin: 16px 0;

  :deep(.el-table) {
    font-size: 13px;

    .el-input__wrapper,
    .el-input-number {
      width: 100%;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
