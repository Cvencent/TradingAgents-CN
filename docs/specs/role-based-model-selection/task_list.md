# 角色化模型选择配置系统 - 任务清单

## Phase 1: 后端基础（预计 2-3 天）

### 1.1 数据模型创建
- [ ] **创建 `app/models/role_model_config.py`**
  - [ ] `RoleModelConfig` 模型
  - [ ] `ModelSelectionPreset` 模型
  - [ ] `AnalysisModelConfig` 模型
  - [ ] `ModelConfigRef` 辅助模型
  - [ ] `RoleModelConfigRef` 辅助模型

### 1.2 数据库集合初始化
- [ ] **创建 `app/db/init_role_model_configs.py`**
  - [ ] 初始化 `role_model_configs` 集合
  - [ ] 初始化 `model_selection_presets` 集合
  - [ ] 插入默认角色配置数据
  - [ ] 插入系统预设数据

### 1.3 服务层开发
- [ ] **创建 `app/services/role_model_config_service.py`**
  - [ ] `get_all_role_configs()` - 获取所有角色配置
  - [ ] `get_role_config(role_id)` - 获取单个角色配置
  - [ ] `update_role_config(role_id, config)` - 更新角色配置
  - [ ] `batch_update_role_configs(configs)` - 批量更新
  - [ ] `get_active_config()` - 获取当前生效配置
  - [ ] `apply_preset(preset_id)` - 应用预设
  - [ ] `get_all_presets()` - 获取所有预设
  - [ ] `create_preset(data)` - 创建预设
  - [ ] `update_preset(preset_id, data)` - 更新预设
  - [ ] `delete_preset(preset_id)` - 删除预设

### 1.4 API 路由开发
- [ ] **创建 `app/routers/role_model_config.py`**
  - [ ] `GET /api/config/role-models` - 获取所有角色配置
  - [ ] `GET /api/config/role-models/{role_id}` - 获取单个角色配置
  - [ ] `PUT /api/config/role-models/{role_id}` - 更新角色配置
  - [ ] `PUT /api/config/role-models/batch` - 批量更新
  - [ ] `GET /api/config/model-presets` - 获取所有预设
  - [ ] `POST /api/config/model-presets` - 创建预设
  - [ ] `PUT /api/config/model-presets/{preset_id}` - 更新预设
  - [ ] `DELETE /api/config/model-presets/{preset_id}` - 删除预设
  - [ ] `POST /api/config/model-presets/{preset_id}/apply` - 应用预设
  - [ ] `GET /api/config/model-selection/active` - 获取当前生效配置

### 1.5 注册路由
- [ ] **修改 `app/main.py`**
  - [ ] 导入 `role_model_config` 路由
  - [ ] 注册路由到 FastAPI 应用

---

## Phase 2: 前端页面（预计 2-3 天）

### 2.1 API 模块
- [ ] **创建 `frontend/src/api/roleModelConfig.ts`**
  - [ ] `getAllRoleConfigs()` - 获取所有角色配置
  - [ ] `updateRoleConfig(roleId, config)` - 更新角色配置
  - [ ] `batchUpdateRoleConfigs(configs)` - 批量更新
  - [ ] `getAllPresets()` - 获取所有预设
  - [ ] `createPreset(data)` - 创建预设
  - [ ] `updatePreset(presetId, data)` - 更新预设
  - [ ] `deletePreset(presetId)` - 删除预设
  - [ ] `applyPreset(presetId)` - 应用预设
  - [ ] `getActiveConfig()` - 获取当前生效配置

### 2.2 类型定义
- [ ] **创建 `frontend/src/types/roleModelConfig.ts`**
  - [ ] `RoleModelConfig` 接口
  - [ ] `ModelSelectionPreset` 接口
  - [ ] `AnalysisModelConfig` 接口
  - [ ] `RoleType` 枚举
  - [ ] `RoleInfo` 接口

### 2.3 组件开发
- [ ] **创建 `frontend/src/views/Settings/components/RoleModelConfigCard.vue`**
  - [ ] 角色信息展示（图标、名称）
  - [ ] 启用/禁用开关
  - [ ] 厂家选择下拉框
  - [ ] 模型选择下拉框
  - [ ] 温度滑块
  - [ ] 高级设置折叠面板
  - [ ] 表单验证

- [ ] **创建 `frontend/src/views/Settings/components/ModelSelectionPresetDialog.vue`**
  - [ ] 预设列表展示
  - [ ] 预设应用按钮
  - [ ] 预设编辑/删除按钮
  - [ ] 创建新预设按钮
  - [ ] 预设详情展示

- [ ] **创建 `frontend/src/views/Settings/components/CreatePresetDialog.vue`**
  - [ ] 预设名称输入
  - [ ] 预设描述输入
  - [ ] 角色配置表格
  - [ ] 默认配置设置
  - [ ] 保存/取消按钮

### 2.4 主页面开发
- [ ] **创建 `frontend/src/views/Settings/RoleModelConfig.vue`**
  - [ ] 页面布局（左侧分类菜单 + 右侧配置卡片）
  - [ ] 角色分类切换（分析师/辩论者/决策者）
  - [ ] 快速预设按钮
  - [ ] 保存/重置按钮
  - [ ] 加载状态处理
  - [ ] 错误提示
  - [ ] 成功提示

### 2.5 路由配置
- [ ] **修改 `frontend/src/router/index.ts`**
  - [ ] 添加角色模型配置路由
  - [ ] 配置菜单项

### 2.6 配置管理页面集成
- [ ] **修改 `frontend/src/views/Settings/ConfigManagement.vue`**
  - [ ] 在菜单中添加"角色模型配置"选项
  - [ ] 配置路由切换

---

## Phase 3: 分析流程集成（预计 1-2 天）

### 3.1 配置读取集成
- [ ] **修改 `tradingagents/agents/trading_agents.py`**
  - [ ] 添加 `_load_role_model_config()` 方法
  - [ ] 在 `__init__` 中调用配置加载
  - [ ] 添加配置缓存机制

### 3.2 分析师模型配置
- [ ] **修改分析师创建逻辑**
  - [ ] `tradingagents/agents/analysts/market_analyst.py`
  - [ ] `tradingagents/agents/analysts/fundamentals_analyst.py`
  - [ ] `tradingagents/agents/analysts/capital_flow_analyst.py`
  - [ ] `tradingagents/agents/analysts/news_analyst.py`
  - [ ] `tradingagents/agents/analysts/social_media_analyst.py`
  - [ ] `tradingagents/agents/analysts/market_trend_analyst.py`

### 3.3 辩论者模型配置
- [ ] **修改辩论者创建逻辑**
  - [ ] 查找辩论者创建代码
  - [ ] 集成角色模型配置

### 3.4 决策者模型配置
- [ ] **修改决策者创建逻辑**
  - [ ] 查找决策者创建代码
  - [ ] 集成角色模型配置

### 3.5 配置回退机制
- [ ] **实现配置优先级逻辑**
  - [ ] 角色特定配置
  - [ ] 角色类型默认配置
  - [ ] 全局默认配置

---

## Phase 4: 优化完善（预计 1 天）

### 4.1 配置验证
- [ ] **后端验证**
  - [ ] 验证模型名称存在性
  - [ ] 验证厂家配置完整性
  - [ ] 验证参数范围

- [ ] **前端验证**
  - [ ] 表单字段验证
  - [ ] 模型选择联动验证

### 4.2 批量操作
- [ ] **批量设置功能**
  - [ ] 批量启用/禁用
  - [ ] 批量应用预设
  - [ ] 批量复制配置

### 4.3 导入导出
- [ ] **配置导入导出**
  - [ ] 导出当前配置为 JSON
  - [ ] 从 JSON 导入配置
  - [ ] 配置分享功能

### 4.4 用户体验优化
- [ ] **加载优化**
  - [ ] 配置缓存
  - [ ] 懒加载
  - [ ] 骨架屏

- [ ] **提示优化**
  - [ ] 配置变更提示
  - [ ] 模型推荐提示
  - [ ] 成本估算提示

---

## 测试清单

### 单元测试
- [ ] RoleModelConfigService 测试
- [ ] API 路由测试
- [ ] 配置优先级逻辑测试

### 集成测试
- [ ] 前端页面交互测试
- [ ] API 集成测试
- [ ] 分析流程集成测试

### 端到端测试
- [ ] 完整配置流程测试
- [ ] 预设应用测试
- [ ] 分析任务模型选择验证

---

## 文档清单

- [ ] **API 文档更新**
  - [ ] Swagger 文档更新
  - [ ] API 使用示例

- [ ] **用户文档**
  - [ ] 功能使用说明
  - [ ] 配置最佳实践
  - [ ] 故障排除指南

- [ ] **开发文档**
  - [ ] 架构设计文档
  - [ ] 代码注释完善

---

## 依赖检查

### 后端依赖
- [ ] 确认 MongoDB 版本支持
- [ ] 确认 Pydantic 版本兼容
- [ ] 确认 FastAPI 版本兼容

### 前端依赖
- [ ] 确认 Element Plus 版本
- [ ] 确认 Vue 3 版本
- [ ] 确认 TypeScript 版本

---

## 部署检查

### 数据库迁移
- [ ] 创建集合脚本
- [ ] 初始化数据脚本
- [ ] 回滚脚本

### 配置检查
- [ ] 环境变量检查
- [ ] 权限配置检查
- [ ] 日志配置检查

---

## 进度追踪

| Phase | 预计时间 | 实际时间 | 状态 | 完成日期 |
|-------|----------|----------|------|----------|
| Phase 1: 后端基础 | 2-3 天 | - | ⏳ 待开始 | - |
| Phase 2: 前端页面 | 2-3 天 | - | ⏳ 待开始 | - |
| Phase 3: 分析流程集成 | 1-2 天 | - | ⏳ 待开始 | - |
| Phase 4: 优化完善 | 1 天 | - | ⏳ 待开始 | - |
| **总计** | **6-9 天** | - | - | - |

---

## 备注

- 优先级：高
- 阻塞项：无
- 风险点：
  - 分析流程集成可能影响现有功能
  - 需要确保向后兼容
- 建议：
  - 分阶段实施，每阶段完成后进行测试
  - 保持与现有配置系统的兼容性
