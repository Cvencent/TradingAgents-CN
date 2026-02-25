<template>
  <el-card
    class="role-model-card"
    :class="{ disabled: !localConfig.is_enabled }"
    shadow="hover"
  >
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="role-info">
        <el-icon :size="24" class="role-icon">
          <component :is="roleInfo.icon" />
        </el-icon>
        <div class="role-text">
          <span class="role-name">{{ roleInfo.name }}</span>
          <span class="role-description">{{ roleInfo.description }}</span>
        </div>
        <el-tag v-if="localConfig.is_default" type="success" size="small" effect="plain">
          默认
        </el-tag>
      </div>
      <div class="card-actions">
        <el-switch
          v-model="localConfig.is_enabled"
          @change="handleEnabledChange"
          inline-prompt
          active-text="启用"
          inactive-text="禁用"
        />
      </div>
    </div>

    <!-- 配置表单 -->
    <div v-show="localConfig.is_enabled" class="config-form">
      <el-form
        ref="formRef"
        :model="localConfig"
        label-width="100px"
        size="default"
      >
        <!-- 厂家选择 -->
        <el-form-item label="厂家">
          <el-select
            v-model="localConfig.provider"
            placeholder="选择厂家"
            filterable
            @change="handleProviderChange"
            style="width: 100%"
          >
            <el-option
              v-for="provider in providers"
              :key="provider.name"
              :label="provider.display_name"
              :value="provider.name"
            />
          </el-select>
        </el-form-item>

        <!-- 模型选择 -->
        <el-form-item label="模型">
          <el-select
            v-model="localConfig.model_name"
            placeholder="选择模型"
            :disabled="!localConfig.provider"
            filterable
            allow-create
            default-first-option
            reserve-keyword
            style="width: 100%"
          >
            <el-option
              v-for="model in availableModels"
              :key="model.name"
              :label="model.display_name || model.name"
              :value="model.name"
            />
          </el-select>
        </el-form-item>

        <!-- 温度参数 -->
        <el-form-item label="温度">
          <div class="slider-with-value">
            <el-slider
              v-model="localConfig.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              style="flex: 1"
            />
            <span class="slider-value">{{ localConfig.temperature }}</span>
          </div>
        </el-form-item>

        <!-- 高级设置 -->
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="高级设置" name="advanced">
            <el-form-item label="最大Token">
              <el-input-number
                v-model="localConfig.max_tokens"
                :min="1000"
                :max="8000"
                :step="1000"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="超时时间">
              <el-input-number
                v-model="localConfig.timeout"
                :min="30"
                :max="300"
                :step="30"
                style="width: 100%"
              >
                <template #suffix>秒</template>
              </el-input-number>
            </el-form-item>

            <el-form-item label="配置说明">
              <el-input
                v-model="localConfig.description"
                type="textarea"
                :rows="2"
                placeholder="可选：添加配置说明"
              />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
      </el-form>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { FormInstance } from 'element-plus'
import {
  TrendCharts,
  Document,
  Money,
  Message,
  ChatDotRound,
  DataLine,
  Top,
  Bottom,
  User,
  Collection,
  Warning
} from '@element-plus/icons-vue'
import type {
  RoleInfo,
  RoleModelConfig,
  RoleModelConfigUpdate
} from '@/types/roleModelConfig'

// 图标映射
const iconMap: Record<string, any> = {
  TrendCharts,
  Document,
  Money,
  Message,
  ChatDotRound,
  DataLine,
  Top,
  Bottom,
  User,
  Collection,
  Warning
}

interface Props {
  roleInfo: RoleInfo
  config: RoleModelConfig | null
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
  update: [roleId: string, config: RoleModelConfigUpdate]
  enabledChange: [roleId: string, enabled: boolean]
}>()

// 本地配置状态
const localConfig = ref<RoleModelConfigUpdate & { is_enabled: boolean }>({
  provider: '',
  model_name: '',
  model_display_name: '',
  temperature: 0.7,
  max_tokens: 4000,
  timeout: 180,
  is_enabled: true,
  description: ''
})

const formRef = ref<FormInstance>()
const activeCollapse = ref<string[]>([])

// 计算可用模型列表
const availableModels = computed(() => {
  if (!localConfig.value.provider) return []
  const provider = props.providers.find(p => p.name === localConfig.value.provider)
  return provider?.models || []
})

// 监听外部配置变化
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig) {
      localConfig.value = {
        provider: newConfig.provider,
        model_name: newConfig.model_name,
        model_display_name: newConfig.model_display_name || '',
        temperature: newConfig.temperature,
        max_tokens: newConfig.max_tokens,
        timeout: newConfig.timeout,
        is_enabled: newConfig.is_enabled,
        description: newConfig.description || ''
      }
    }
  },
  { immediate: true, deep: true }
)

// 监听本地配置变化并触发更新
watch(
  localConfig,
  (newConfig) => {
    if (newConfig.is_enabled) {
      emit('update', props.roleInfo.id, {
        provider: newConfig.provider,
        model_name: newConfig.model_name,
        model_display_name: newConfig.model_display_name,
        temperature: newConfig.temperature,
        max_tokens: newConfig.max_tokens,
        timeout: newConfig.timeout,
        is_enabled: newConfig.is_enabled,
        description: newConfig.description
      })
    }
  },
  { deep: true }
)

// 处理启用状态变化
const handleEnabledChange = (enabled: boolean) => {
  emit('enabledChange', props.roleInfo.id, enabled)
  if (enabled) {
    // 启用时触发更新
    emit('update', props.roleInfo.id, {
      provider: localConfig.value.provider,
      model_name: localConfig.value.model_name,
      model_display_name: localConfig.value.model_display_name,
      temperature: localConfig.value.temperature,
      max_tokens: localConfig.value.max_tokens,
      timeout: localConfig.value.timeout,
      is_enabled: true,
      description: localConfig.value.description
    })
  }
}

// 处理厂家变化
const handleProviderChange = (providerName: string) => {
  localConfig.value.model_name = ''
  localConfig.value.model_display_name = ''
}

// 获取配置数据（供父组件调用）
const getConfig = (): RoleModelConfigUpdate & { is_enabled: boolean; role_id: string } => {
  return {
    role_id: props.roleInfo.id,
    ...localConfig.value
  }
}

// 验证表单
const validate = async (): Promise<boolean> => {
  if (!localConfig.value.is_enabled) return true
  if (!formRef.value) return true
  
  try {
    await formRef.value.validate()
    return true
  } catch {
    return false
  }
}

defineExpose({
  getConfig,
  validate
})
</script>

<style scoped lang="scss">
.role-model-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;

  &.disabled {
    opacity: 0.6;
    background-color: var(--el-fill-color-light);
  }

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-light);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.role-info {
  display: flex;
  align-items: center;
  gap: 12px;

  .role-icon {
    color: var(--el-color-primary);
    flex-shrink: 0;
  }

  .role-text {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .role-name {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .role-description {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-form {
  padding-top: 20px;

  :deep(.el-form-item) {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }
}

.slider-with-value {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;

  .slider-value {
    min-width: 40px;
    text-align: right;
    font-size: 14px;
    color: var(--el-text-color-primary);
    font-weight: 500;
  }
}

:deep(.el-collapse) {
  border: none;

  .el-collapse-item__header {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    border-bottom: none;
    padding-left: 0;
  }

  .el-collapse-item__wrap {
    border-bottom: none;
  }

  .el-collapse-item__content {
    padding-bottom: 0;
  }
}
</style>
