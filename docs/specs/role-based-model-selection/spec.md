# 角色化模型选择配置系统 - 技术规格文档

## 1. 项目概述

### 1.1 需求背景
当前系统仅在股票分析页面提供统一的模型选择功能。用户希望实现更细粒度的模型配置，允许为每个分析师（技术面、基本面、资金流、新闻、社媒、大盘走势）以及每个角色（多头、空头、投资经理、组合经理）配置不同的模型。

### 1.2 目标
- 实现角色级别的模型选择配置
- 支持分析师级别的模型选择
- 提供直观的配置界面
- 确保配置在分析流程中正确生效

### 1.3 范围
- 后端：新增模型配置API和数据模型
- 前端：新增模型配置页面
- 集成：修改分析流程以使用新配置

---

## 2. 系统架构

### 2.1 角色定义

#### 2.1.1 分析师角色（Analysts）
| 角色ID | 角色名称 | 说明 |
|--------|----------|------|
| market | 技术面分析师 | 技术分析、价格走势 |
| fundamentals | 基本面分析师 | 财务报表、基本面分析 |
| capital_flow | 资金流分析师 | 主力资金、北向资金 |
| news | 新闻分析师 | 新闻舆情分析 |
| social | 社媒分析师 | 社交媒体情绪 |
| market_trend | 大盘走势分析师 | 大盘指数、行业分析 |

#### 2.1.2 辩论角色（Debaters）
| 角色ID | 角色名称 | 说明 |
|--------|----------|------|
| bull | 多头分析师 | 看涨观点 |
| bear | 空头分析师 | 看跌观点 |

#### 2.1.3 决策角色（Decision Makers）
| 角色ID | 角色名称 | 说明 |
|--------|----------|------|
| investment_manager | 投资经理 | 投资决策 |
| portfolio_manager | 组合经理 | 组合管理 |
| risk_manager | 风险经理 | 风险评估 |

### 2.2 配置层级

```
配置优先级（从高到低）：
1. 具体角色配置（如：market_analyst）
2. 角色类型默认配置（如：analyst_default）
3. 全局默认配置（global_default）
```

---

## 3. 数据模型

### 3.1 核心数据模型

#### 3.1.1 RoleModelConfig（角色模型配置）
```python
class RoleModelConfig(BaseModel):
    """角色模型配置"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # 角色标识
    role_id: str = Field(..., description="角色ID，如：market, bull, investment_manager")
    role_type: str = Field(..., description="角色类型：analyst/debater/decision_maker")
    role_name: str = Field(..., description="角色显示名称")
    
    # 模型配置
    provider: str = Field(..., description="模型厂家")
    model_name: str = Field(..., description="模型名称")
    model_display_name: Optional[str] = Field(None, description="模型显示名称")
    
    # 模型参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000)
    timeout: int = Field(default=180)
    
    # 启用状态
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=False, description="是否为该类型角色的默认配置")
    
    # 元数据
    description: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=now_tz)
    updated_at: datetime = Field(default_factory=now_tz)
    created_by: Optional[str] = Field(None)
```

#### 3.1.2 ModelSelectionPreset（模型选择预设）
```python
class ModelSelectionPreset(BaseModel):
    """模型选择预设方案"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    name: str = Field(..., description="预设名称")
    description: Optional[str] = Field(None)
    
    # 预设类型：system（系统预设）/ user（用户自定义）
    preset_type: str = Field(default="user")
    
    # 角色配置映射
    role_configs: Dict[str, RoleModelConfigRef] = Field(default_factory=dict)
    # 格式：{"market": {"provider": "openai", "model_name": "gpt-4"}, ...}
    
    # 默认配置（当角色没有特定配置时使用）
    default_provider: str = Field(...)
    default_model: str = Field(...)
    
    is_active: bool = Field(default=True)
    is_system: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=now_tz)
    updated_at: datetime = Field(default_factory=now_tz)
```

#### 3.1.3 AnalysisModelConfig（分析模型配置 - 运行时配置）
```python
class AnalysisModelConfig(BaseModel):
    """分析任务模型配置"""
    # 关联的分析任务或用户
    task_id: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)
    
    # 使用的预设
    preset_id: Optional[str] = Field(None)
    
    # 实际使用的模型配置（展开后的完整配置）
    analyst_models: Dict[str, ModelConfigRef] = Field(default_factory=dict)
    debater_models: Dict[str, ModelConfigRef] = Field(default_factory=dict)
    decision_models: Dict[str, ModelConfigRef] = Field(default_factory=dict)
    
    # 默认模型（当特定角色没有配置时使用）
    default_model: ModelConfigRef
    
    created_at: datetime = Field(default_factory=now_tz)
```

### 3.2 辅助数据模型

```python
class ModelConfigRef(BaseModel):
    """模型配置引用"""
    provider: str
    model_name: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None

class RoleModelConfigRef(BaseModel):
    """角色模型配置引用（用于预设）"""
    provider: str
    model_name: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4000
    custom_prompt: Optional[str] = None  # 角色特定的系统提示词覆盖
```

---

## 4. API 设计

### 4.1 角色模型配置 API

#### 4.1.1 获取所有角色配置
```
GET /api/config/role-models

Response:
{
  "success": true,
  "data": {
    "analysts": [
      {
        "role_id": "market",
        "role_name": "技术面分析师",
        "role_type": "analyst",
        "current_config": {
          "provider": "openai",
          "model_name": "gpt-4",
          "temperature": 0.7,
          "max_tokens": 4000
        }
      }
    ],
    "debators": [...],
    "decision_makers": [...]
  }
}
```

#### 4.1.2 更新角色模型配置
```
PUT /api/config/role-models/{role_id}

Request:
{
  "provider": "openai",
  "model_name": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 4000,
  "timeout": 180,
  "description": "技术面分析专用模型"
}

Response:
{
  "success": true,
  "data": {
    "role_id": "market",
    "provider": "openai",
    "model_name": "gpt-4",
    ...
  }
}
```

#### 4.1.3 批量更新角色配置
```
PUT /api/config/role-models/batch

Request:
{
  "configs": [
    {
      "role_id": "market",
      "provider": "openai",
      "model_name": "gpt-4"
    },
    {
      "role_id": "fundamentals",
      "provider": "anthropic",
      "model_name": "claude-3-opus"
    }
  ]
}
```

### 4.2 预设管理 API

#### 4.2.1 获取所有预设
```
GET /api/config/model-presets

Query Parameters:
- preset_type: system | user | all (default: all)
- include_inactive: bool (default: false)
```

#### 4.2.2 创建预设
```
POST /api/config/model-presets

Request:
{
  "name": "高性能分析方案",
  "description": "使用最强模型进行深度分析",
  "role_configs": {
    "market": {
      "provider": "openai",
      "model_name": "gpt-4o",
      "temperature": 0.5
    },
    "fundamentals": {
      "provider": "anthropic",
      "model_name": "claude-3-opus",
      "temperature": 0.3
    },
    "bull": {
      "provider": "openai",
      "model_name": "gpt-4",
      "temperature": 0.8
    },
    "bear": {
      "provider": "openai",
      "model_name": "gpt-4",
      "temperature": 0.8
    },
    "investment_manager": {
      "provider": "openai",
      "model_name": "gpt-4o",
      "temperature": 0.4
    }
  },
  "default_provider": "openai",
  "default_model": "gpt-3.5-turbo"
}
```

#### 4.2.3 应用预设
```
POST /api/config/model-presets/{preset_id}/apply

Response:
{
  "success": true,
  "message": "预设已应用",
  "applied_configs": 8
}
```

### 4.3 运行时配置 API

#### 4.3.1 获取当前生效的配置
```
GET /api/config/model-selection/active

Response:
{
  "success": true,
  "data": {
    "preset_id": "preset_xxx",
    "preset_name": "高性能分析方案",
    "configs": {
      "analysts": {
        "market": { "provider": "openai", "model_name": "gpt-4o", ... },
        "fundamentals": { "provider": "anthropic", "model_name": "claude-3-opus", ... }
      },
      "debaters": {
        "bull": { ... },
        "bear": { ... }
      },
      "decision_makers": {
        "investment_manager": { ... },
        "portfolio_manager": { ... }
      }
    },
    "default_model": { "provider": "openai", "model_name": "gpt-3.5-turbo" }
  }
}
```

---

## 5. 前端设计

### 5.1 页面结构

```
设置 > 配置管理 > 角色模型配置（新标签页）

页面布局：
┌─────────────────────────────────────────────────────────────┐
│ 角色模型配置                                    [保存] [重置] │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  角色分类    │           模型配置卡片                        │
│  ─────────   │                                              │
│  ○ 分析师    │  ┌────────────────────────────────────────┐  │
│  ○ 辩论者    │  │ 技术面分析师        [启用] [默认]        │  │
│  ○ 决策者    │  │ ──────────────────────────────────────  │  │
│              │  │ 厂家: [OpenAI        ▼]                  │  │
│  快速预设    │  │ 模型: [GPT-4        ▼]                   │  │
│  ─────────   │  │                                          │  │
│  [经济型]    │  │ 温度: [━━━●━━━━] 0.7                     │  │
│  [平衡型]    │  │ 最大Token: [4000    ▼]                   │  │
│  [高性能]    │  │ 超时: [180秒      ▼]                     │  │
│              │  │                                          │  │
│              │  │ [高级设置 ▼]                             │  │
│              │  └────────────────────────────────────────┘  │
│              │                                              │
│              │  ┌────────────────────────────────────────┐  │
│              │  │ 基本面分析师        [启用] [默认]        │  │
│              │  │ ──────────────────────────────────────  │  │
│              │  │ ...                                     │  │
│              │  └────────────────────────────────────────┘  │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### 5.2 组件设计

#### 5.2.1 RoleModelConfigCard 组件
```vue
<template>
  <el-card class="role-model-card" :class="{ disabled: !config.is_enabled }">
    <div class="card-header">
      <div class="role-info">
        <el-icon><component :is="roleIcon" /></el-icon>
        <span class="role-name">{{ roleName }}</span>
        <el-tag v-if="config.is_default" type="success" size="small">默认</el-tag>
      </div>
      <div class="card-actions">
        <el-switch v-model="config.is_enabled" />
      </div>
    </div>
    
    <div class="config-form" v-show="config.is_enabled">
      <el-form :model="config" label-width="100px">
        <el-form-item label="厂家">
          <el-select v-model="config.provider" @change="handleProviderChange">
            <el-option 
              v-for="provider in providers" 
              :key="provider.name"
              :label="provider.display_name"
              :value="provider.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型">
          <el-select v-model="config.model_name">
            <el-option
              v-for="model in availableModels"
              :key="model.name"
              :label="model.display_name"
              :value="model.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="温度">
          <el-slider v-model="config.temperature" :min="0" :max="2" :step="0.1" />
        </el-form-item>
        
        <el-collapse>
          <el-collapse-item title="高级设置">
            <el-form-item label="最大Token">
              <el-input-number v-model="config.max_tokens" :min="1000" :max="8000" :step="1000" />
            </el-form-item>
            <el-form-item label="超时时间">
              <el-input-number v-model="config.timeout" :min="30" :max="300" :step="30" />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
      </el-form>
    </div>
  </el-card>
</template>
```

#### 5.2.2 ModelSelectionPresetDialog 组件
```vue
<!-- 预设管理对话框 -->
<template>
  <el-dialog title="模型选择预设" v-model="visible" width="800px">
    <div class="preset-list">
      <el-card v-for="preset in presets" :key="preset.id" class="preset-card">
        <div class="preset-header">
          <h4>{{ preset.name }}</h4>
          <el-tag v-if="preset.is_system" type="info">系统</el-tag>
        </div>
        <p class="preset-description">{{ preset.description }}</p>
        <div class="preset-roles">
          <el-tag v-for="(config, role) in preset.role_configs" :key="role" size="small">
            {{ getRoleName(role) }}: {{ config.model_name }}
          </el-tag>
        </div>
        <div class="preset-actions">
          <el-button type="primary" @click="applyPreset(preset.id)">应用</el-button>
          <el-button v-if="!preset.is_system" @click="editPreset(preset)">编辑</el-button>
          <el-button v-if="!preset.is_system" type="danger" @click="deletePreset(preset.id)">删除</el-button>
        </div>
      </el-card>
    </div>
    <template #footer>
      <el-button type="primary" @click="showCreateDialog">创建新预设</el-button>
    </template>
  </el-dialog>
</template>
```

### 5.3 路由配置
```typescript
// router/index.ts
{
  path: '/settings/config',
  component: ConfigManagement,
  children: [
    // ... 现有路由
    {
      path: 'role-models',
      name: 'RoleModelConfig',
      component: () => import('@/views/Settings/RoleModelConfig.vue'),
      meta: { title: '角色模型配置' }
    }
  ]
}
```

---

## 6. 后端实现

### 6.1 数据库集合设计

```javascript
// role_model_configs 集合
{
  _id: ObjectId,
  role_id: "market",           // 角色ID
  role_type: "analyst",        // 角色类型
  role_name: "技术面分析师",    // 显示名称
  provider: "openai",
  model_name: "gpt-4",
  model_display_name: "GPT-4",
  temperature: 0.7,
  max_tokens: 4000,
  timeout: 180,
  is_enabled: true,
  is_default: false,
  description: "",
  created_at: ISODate,
  updated_at: ISODate
}

// model_selection_presets 集合
{
  _id: ObjectId,
  name: "高性能分析方案",
  description: "使用最强模型进行深度分析",
  preset_type: "user",         // system | user
  role_configs: {
    "market": {
      provider: "openai",
      model_name: "gpt-4o",
      temperature: 0.5
    },
    "fundamentals": {
      provider: "anthropic",
      model_name: "claude-3-opus"
    }
  },
  default_provider: "openai",
  default_model: "gpt-3.5-turbo",
  is_active: true,
  is_system: false,
  created_at: ISODate,
  updated_at: ISODate
}
```

### 6.2 服务层设计

```python
# app/services/role_model_config_service.py

class RoleModelConfigService:
    """角色模型配置服务"""
    
    # 预定义角色
    ANALYST_ROLES = [
        {"id": "market", "name": "技术面分析师", "icon": "TrendCharts"},
        {"id": "fundamentals", "name": "基本面分析师", "icon": "Document"},
        {"id": "capital_flow", "name": "资金流分析师", "icon": "Money"},
        {"id": "news", "name": "新闻分析师", "icon": "News"},
        {"id": "social", "name": "社媒分析师", "icon": "ChatDotRound"},
        {"id": "market_trend", "name": "大盘走势分析师", "icon": "DataLine"},
    ]
    
    DEBATER_ROLES = [
        {"id": "bull", "name": "多头分析师", "icon": "Top"},
        {"id": "bear", "name": "空头分析师", "icon": "Bottom"},
    ]
    
    DECISION_ROLES = [
        {"id": "investment_manager", "name": "投资经理", "icon": "User"},
        {"id": "portfolio_manager", "name": "组合经理", "icon": "Collection"},
        {"id": "risk_manager", "name": "风险经理", "icon": "Warning"},
    ]
    
    async def get_all_role_configs(self) -> Dict[str, List[RoleModelConfig]]:
        """获取所有角色配置"""
        pass
    
    async def update_role_config(self, role_id: str, config: RoleModelConfigUpdate) -> RoleModelConfig:
        """更新角色配置"""
        pass
    
    async def get_active_config(self) -> AnalysisModelConfig:
        """获取当前生效的配置"""
        pass
    
    async def apply_preset(self, preset_id: str) -> bool:
        """应用预设配置"""
        pass
```

### 6.3 集成到分析流程

```python
# tradingagents/agents/trading_agents.py

class TradingAgents:
    def __init__(self, ...):
        # 获取角色模型配置
        self.model_config = self._load_role_model_config()
    
    def _load_role_model_config(self) -> AnalysisModelConfig:
        """加载角色模型配置"""
        from app.services.role_model_config_service import RoleModelConfigService
        service = RoleModelConfigService()
        return await service.get_active_config()
    
    def _create_analyst(self, analyst_type: str, ...):
        """创建分析师，使用对应的模型配置"""
        # 获取该分析师的模型配置
        model_config = self.model_config.get_analyst_model(analyst_type)
        
        # 使用配置的模型创建LLM
        llm = self._create_llm_from_config(model_config)
        
        # 创建分析师
        return create_analyst(analyst_type, llm, ...)
    
    def _create_debater(self, position: str, ...):
        """创建辩论者，使用对应的模型配置"""
        model_config = self.model_config.get_debater_model(position)
        llm = self._create_llm_from_config(model_config)
        return create_debater(position, llm, ...)
```

---

## 7. 实现步骤

### Phase 1: 后端基础（2-3天）
1. **数据模型**
   - [ ] 创建 RoleModelConfig 模型
   - [ ] 创建 ModelSelectionPreset 模型
   - [ ] 创建 AnalysisModelConfig 模型

2. **数据库**
   - [ ] 创建 role_model_configs 集合
   - [ ] 创建 model_selection_presets 集合
   - [ ] 初始化默认角色配置

3. **API 开发**
   - [ ] 实现角色配置 CRUD API
   - [ ] 实现预设管理 API
   - [ ] 实现运行时配置 API

### Phase 2: 前端页面（2-3天）
1. **组件开发**
   - [ ] 创建 RoleModelConfigCard 组件
   - [ ] 创建 ModelSelectionPresetDialog 组件
   - [ ] 创建 RoleModelConfig 主页面

2. **API 集成**
   - [ ] 创建 roleModelConfig.ts API 模块
   - [ ] 集成到页面

### Phase 3: 分析流程集成（1-2天）
1. **配置读取**
   - [ ] 修改 TradingAgents 类读取角色配置
   - [ ] 修改分析师创建逻辑
   - [ ] 修改辩论者创建逻辑

2. **测试验证**
   - [ ] 验证配置正确生效
   - [ ] 验证默认配置回退

### Phase 4: 优化完善（1天）
1. **用户体验**
   - [ ] 添加配置验证
   - [ ] 添加批量操作
   - [ ] 添加导入导出

---

## 8. 接口兼容性

### 8.1 向后兼容
- 现有分析流程不指定模型时，使用新的角色配置
- 现有模型配置页面保留，作为"全局默认配置"
- 角色配置未设置时，自动回退到全局默认配置

### 8.2 配置优先级
```python
def get_model_for_role(role_id: str) -> ModelConfig:
    """获取角色的模型配置，按优先级查找"""
    # 1. 查找角色特定配置
    config = get_role_config(role_id)
    if config and config.is_enabled:
        return config
    
    # 2. 查找角色类型默认配置
    role_type = get_role_type(role_id)
    default_config = get_default_config_for_type(role_type)
    if default_config and default_config.is_enabled:
        return default_config
    
    # 3. 使用全局默认配置
    return get_global_default_config()
```

---

## 9. 安全考虑

1. **权限控制**
   - 角色配置修改需要管理员权限
   - 预设管理需要管理员权限
   - 普通用户只能查看和选择预设

2. **配置验证**
   - 验证模型名称在厂家模型列表中存在
   - 验证厂家配置完整（API Key等）
   - 验证参数范围合法

3. **审计日志**
   - 记录配置修改操作
   - 记录预设应用操作
   - 记录配置变更历史

---

## 10. 附录

### 10.1 角色图标映射
```python
ROLE_ICONS = {
    # 分析师
    "market": "TrendCharts",
    "fundamentals": "Document",
    "capital_flow": "Money",
    "news": "News",
    "social": "ChatDotRound",
    "market_trend": "DataLine",
    # 辩论者
    "bull": "Top",
    "bear": "Bottom",
    # 决策者
    "investment_manager": "User",
    "portfolio_manager": "Collection",
    "risk_manager": "Warning",
}
```

### 10.2 预设模板
```python
DEFAULT_PRESETS = [
    {
        "name": "经济型",
        "description": "使用成本较低的模型，适合快速分析",
        "role_configs": {
            "default": {"provider": "openai", "model_name": "gpt-3.5-turbo"}
        }
    },
    {
        "name": "平衡型",
        "description": "在成本和性能之间取得平衡",
        "role_configs": {
            "market": {"provider": "openai", "model_name": "gpt-4"},
            "fundamentals": {"provider": "openai", "model_name": "gpt-4"},
            "default": {"provider": "openai", "model_name": "gpt-3.5-turbo"}
        }
    },
    {
        "name": "高性能",
        "description": "使用最强模型，适合深度分析",
        "role_configs": {
            "market": {"provider": "openai", "model_name": "gpt-4o"},
            "fundamentals": {"provider": "anthropic", "model_name": "claude-3-opus"},
            "capital_flow": {"provider": "openai", "model_name": "gpt-4"},
            "news": {"provider": "openai", "model_name": "gpt-4"},
            "social": {"provider": "openai", "model_name": "gpt-4"},
            "market_trend": {"provider": "openai", "model_name": "gpt-4"},
            "bull": {"provider": "openai", "model_name": "gpt-4"},
            "bear": {"provider": "openai", "model_name": "gpt-4"},
            "investment_manager": {"provider": "openai", "model_name": "gpt-4o"},
            "default": {"provider": "openai", "model_name": "gpt-4"}
        }
    }
]
```
