import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from app.services.analysis_workflow_service import MongoAnalysisWorkflowConfig

db = get_mongo_db_sync()

# 删除现有的系统预设（analysis_level为None或错误的数据）
result = db.analysis_workflow_configs.delete_many({"is_system": True})
print(f'删除了 {result.deleted_count} 条系统预设')

# 重新初始化
workflow_service = MongoAnalysisWorkflowConfig(db)
result = workflow_service.initialize_system_presets()
print(f'初始化结果: {result}')

# 验证
configs = list(db.analysis_workflow_configs.find({}))
print(f'共找到 {len(configs)} 条配置:')
for c in configs:
    level = c.get("analysis_level")
    print(f'  - {c.get("name")}: analysis_level = {level!r}')
