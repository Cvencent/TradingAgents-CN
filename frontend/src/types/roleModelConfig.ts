/**
 * 角色模型配置类型定义
 */

// ==================== 基础类型 ====================

/** 角色类型 */
export type RoleType = 'analyst' | 'debater' | 'decision_maker'

/** 模型配置引用 */
export interface ModelConfigRef {
  provider: string
  model_name: string
  temperature?: number
  max_tokens?: number
  timeout?: number
}

/** 角色模型配置引用（用于预设） */
export interface RoleModelConfigRef {
  provider: string
  model_name: string
  temperature?: number
  max_tokens?: number
  custom_prompt?: string
}

// ==================== 角色配置 ====================

/** 角色信息 */
export interface RoleInfo {
  id: string
  name: string
  type: RoleType
  icon: string
  description: string
}

/** 角色模型配置 */
export interface RoleModelConfig {
  id?: string
  role_id: string
  role_type: RoleType
  role_name: string
  provider: string
  model_name: string
  model_display_name?: string
  temperature: number
  max_tokens: number
  timeout: number
  is_enabled: boolean
  is_default: boolean
  description?: string
  created_at?: string
  updated_at?: string
}

/** 角色配置响应（包含角色信息和当前配置） */
export interface RoleConfigResponse {
  role_id: string
  role_name: string
  role_type: RoleType
  icon: string
  description: string
  current_config: RoleModelConfig | null
}

/** 所有角色配置响应 */
export interface RoleConfigsResponse {
  analysts: RoleConfigResponse[]
  debaters: RoleConfigResponse[]
  decision_makers: RoleConfigResponse[]
}

/** 角色配置更新请求 */
export interface RoleModelConfigUpdate {
  provider: string
  model_name: string
  model_display_name?: string
  temperature: number
  max_tokens: number
  timeout: number
  is_enabled: boolean
  description?: string
}

// ==================== 预设 ====================

/** 模型选择预设 */
export interface ModelSelectionPreset {
  id?: string
  name: string
  description?: string
  preset_type: 'system' | 'user'
  role_configs: Record<string, RoleModelConfigRef>
  default_provider: string
  default_model: string
  is_active: boolean
  is_system: boolean
  created_at?: string
  updated_at?: string
}

/** 创建预设请求 */
export interface ModelSelectionPresetCreate {
  name: string
  description?: string
  role_configs: Record<string, RoleModelConfigRef>
  default_provider: string
  default_model: string
}

/** 更新预设请求 */
export interface ModelSelectionPresetUpdate {
  name?: string
  description?: string
  role_configs?: Record<string, RoleModelConfigRef>
  default_provider?: string
  default_model?: string
  is_active?: boolean
}

/** 应用预设响应 */
export interface ApplyPresetResponse {
  success: boolean
  message: string
  applied_configs: number
}

// ==================== 运行时配置 ====================

/** 当前生效的配置 */
export interface ActiveModelConfig {
  preset_id?: string
  preset_name?: string
  configs: {
    analysts: Record<string, ModelConfigRef>
    debaters: Record<string, ModelConfigRef>
    decision_makers: Record<string, ModelConfigRef>
  }
  default_model?: ModelConfigRef
}

// ==================== 预定义角色 ====================

/** 分析师角色 */
export const ANALYST_ROLES: RoleInfo[] = [
  { id: 'market', name: '技术面分析师', type: 'analyst', icon: 'TrendCharts', description: '技术分析、价格走势分析' },
  { id: 'fundamentals', name: '基本面分析师', type: 'analyst', icon: 'Document', description: '财务报表、基本面分析' },
  { id: 'capital_flow', name: '资金流分析师', type: 'analyst', icon: 'Money', description: '主力资金、北向资金分析' },
  { id: 'news', name: '新闻分析师', type: 'analyst', icon: 'Message', description: '新闻舆情分析' },
  { id: 'social', name: '社媒分析师', type: 'analyst', icon: 'ChatDotRound', description: '社交媒体情绪分析' },
  { id: 'market_trend', name: '大盘走势分析师', type: 'analyst', icon: 'DataLine', description: '大盘指数、行业分析' }
]

/** 辩论者角色 */
export const DEBATER_ROLES: RoleInfo[] = [
  { id: 'bull', name: '多头分析师', type: 'debater', icon: 'Top', description: '看涨观点分析' },
  { id: 'bear', name: '空头分析师', type: 'debater', icon: 'Bottom', description: '看跌观点分析' }
]

/** 决策者角色 */
export const DECISION_ROLES: RoleInfo[] = [
  { id: 'investment_manager', name: '投资经理', type: 'decision_maker', icon: 'User', description: '投资决策' },
  { id: 'portfolio_manager', name: '组合经理', type: 'decision_maker', icon: 'Collection', description: '组合管理' },
  { id: 'risk_manager', name: '风险经理', type: 'decision_maker', icon: 'Warning', description: '风险评估' }
]

/** 所有角色 */
export const ALL_ROLES: RoleInfo[] = [...ANALYST_ROLES, ...DEBATER_ROLES, ...DECISION_ROLES]

/** 角色类型显示名称 */
export const ROLE_TYPE_NAMES: Record<RoleType, string> = {
  analyst: '分析师',
  debater: '辩论者',
  decision_maker: '决策者'
}

/** 获取角色信息 */
export function getRoleInfo(roleId: string): RoleInfo | undefined {
  return ALL_ROLES.find(role => role.id === roleId)
}

/** 获取角色类型 */
export function getRoleType(roleId: string): RoleType | undefined {
  return getRoleInfo(roleId)?.type
}
