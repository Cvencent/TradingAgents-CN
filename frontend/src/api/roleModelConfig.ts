/**
 * 角色模型配置 API
 */

import request from '@/api/request'
import type { ApiResponse } from '@/api/request'
import type {
  RoleModelConfig,
  RoleModelConfigUpdate,
  ModelSelectionPreset,
  ModelSelectionPresetCreate,
  ModelSelectionPresetUpdate,
  ActiveModelConfig,
  ApplyPresetResponse,
  RoleConfigsResponse
} from '@/types/roleModelConfig'

/**
 * 获取所有角色配置
 */
export function getAllRoleConfigs(): Promise<ApiResponse<RoleConfigsResponse>> {
  return request.get('/api/config/role-models')
}

/**
 * 获取单个角色配置
 */
export function getRoleConfig(roleId: string): Promise<ApiResponse<RoleModelConfig>> {
  return request.get(`/api/config/role-models/${roleId}`)
}

/**
 * 更新角色配置
 */
export function updateRoleConfig(
  roleId: string,
  data: RoleModelConfigUpdate
): Promise<ApiResponse<RoleModelConfig>> {
  return request.put(`/api/config/role-models/${roleId}`, data)
}

/**
 * 批量更新角色配置
 */
export function batchUpdateRoleConfigs(
  configs: (RoleModelConfigUpdate & { role_id: string })[]
): Promise<ApiResponse<{ success: string[]; failed: { role_id?: string; error: string }[] }>> {
  return request.put('/api/config/role-models/batch', { configs })
}

/**
 * 获取所有预设
 */
export function getAllPresets(
  presetType?: string,
  includeInactive?: boolean
): Promise<ApiResponse<ModelSelectionPreset[]>> {
  return request.get('/api/config/model-presets', {
    params: {
      preset_type: presetType,
      include_inactive: includeInactive
    }
  })
}

/**
 * 获取单个预设
 */
export function getPreset(presetId: string): Promise<ApiResponse<ModelSelectionPreset>> {
  return request.get(`/api/config/model-presets/${presetId}`)
}

/**
 * 创建预设
 */
export function createPreset(
  data: ModelSelectionPresetCreate
): Promise<ApiResponse<ModelSelectionPreset>> {
  return request.post('/api/config/model-presets', data)
}

/**
 * 更新预设
 */
export function updatePreset(
  presetId: string,
  data: ModelSelectionPresetUpdate
): Promise<ApiResponse<ModelSelectionPreset>> {
  return request.put(`/api/config/model-presets/${presetId}`, data)
}

/**
 * 删除预设
 */
export function deletePreset(presetId: string): Promise<ApiResponse<void>> {
  return request.delete(`/api/config/model-presets/${presetId}`)
}

/**
 * 应用预设
 */
export function applyPreset(presetId: string): Promise<ApiResponse<ApplyPresetResponse>> {
  return request.post(`/api/config/model-presets/${presetId}/apply`)
}

/**
 * 获取当前生效的配置
 */
export function getActiveConfig(): Promise<ApiResponse<ActiveModelConfig>> {
  return request.get('/api/config/model-selection/active')
}

/**
 * 获取指定角色的模型配置
 */
export function getModelForRole(roleId: string): Promise<ApiResponse<RoleModelConfig>> {
  return request.get(`/api/config/model-selection/role/${roleId}`)
}
