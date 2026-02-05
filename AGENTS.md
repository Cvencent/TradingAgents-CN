# AGENTS.md - Coding Guidelines for TradingAgents-CN

This guide helps agentic coding assistants work effectively with the TradingAgents-CN codebase.

## Build, Lint, and Test Commands

### Installation
```bash
# Install in development mode
pip install -e .

# Or using uv (recommended for faster installation)
uv pip install -e .
```

### Running Tests
```bash
# Run a specific test file
python tests/test_analysis.py

# Run a test from the tests/ directory
cd tests && python test_google.py

# Run unit tests in specific subdirectory
python tests/unit/tools/analysis/test_indicators_uil.py
```

Note: Tests are Python scripts run directly, not through pytest. There's no central test runner defined.

### No Lint/Format Commands Configured
This project does not have standard linting/formatting tools configured (no pyproject.toml [tool.*] sections for black, ruff, flake8, mypy, etc.). Follow the existing code style patterns.

---

## Code Style Guidelines

### Import Ordering
1. Standard library imports first (os, sys, pathlib, datetime, typing, json, etc.)
2. Third-party imports second (langchain, pandas, numpy, openai, etc.)
3. Local imports third (tradingagents.* modules)

```python
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from langchain_openai import ChatOpenAI
import pandas as pd

from tradingagents.utils.logging_manager import get_logger
```

### Import Conventions
- Use explicit imports: `from module import function, Class`
- Avoid wildcard imports (`from module import *`) except in `__init__.py` files
- Relative imports for sibling modules: `from .module import Class`

### Formatting
- **Indentation**: 4 spaces (no tabs)
- **Line length**: Generally under 100-120 characters, some longer lines acceptable
- **Blank lines**: 2 blank lines between top-level definitions, 1 between methods

### Type Annotations
- Use `typing` module for type hints: `Dict`, `List`, `Optional`, `Any`, `Union`, `Tuple`
- Use `TypedDict` from `typing_extensions` for structured state/data classes
- Use `Annotated` for fields with additional metadata

```python
from typing import Dict, Any, Optional, List, Tuple
from typing_extensions import TypedDict, Annotated

class AgentState(TypedDict):
    company_of_interest: Annotated[str, "Company description"]
    market_report: Annotated[str, "Report from market analyst"]  
    tool_call_count: Annotated[int, "Tool invocation counter"]

def create_llm(provider: str, model: str, config: Dict[str, Any]) -> Optional[ChatOpenAI]:
    pass
```

### Naming Conventions
- **Classes**: PascalCase (`TradingAgentsGraph`, `ColoredFormatter`, `FinancialSituationMemory`)
- **Functions/Methods**: snake_case (`create_llm_by_provider`, `get_logger`, `propagate`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_CONFIG`, `COLORS`, `MAX_ROUNDS`)
- **Private methods**: _prefix (`_setup_logging`, `_load_config`, `_create_tool_nodes`)
- **Module variables**: snake_case or UPPER_SNAKE_CASE for config dicts

### Docstrings
- Use triple-quoted strings with Args: and Returns: sections
- Include Chinese descriptions for user-facing messages, English for technical comments

```python
def create_bull_researcher(llm: ChatOpenAI, memory: Optional[FinancialSituationMemory]):
    """
    Create a bullish researcher agent node.

    Args:
        llm: Language model instance for generating responses
        memory: Optional memory instance for retrieving past experiences

    Returns:
        A callable function that processes agent state
    """
```

### Error Handling
- Use `try-except` blocks with specific exception types
- Log errors using the unified logging system: `logger.error()`, `logger.warning()`
- Raise `ValueError` for configuration/validation issues
- Provide clear, descriptive error messages

```python
from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")

try:
    result = some_operation()
except KeyError as e:
    logger.error(f"Missing required key: {e}")
    raise ValueError(f"Configuration error: missing key {e}")
```

### Logging
- Use unified logging system: `from tradingagents.utils.logging_init import get_logger`
- Get logger with module name: `logger = get_logger("module_name")`
- Log levels: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`
- Use emoji prefixes for clarity: `✅`, `❌`, `⚠️`, `🔧`, `🚀`
- Include context in log messages: stock symbol, function name, operation

```python
logger.info(f"🚀 开始分析 - 股票: {ticker}")
logger.debug(f"🔧 [DEBUG] 参数: {params}")
logger.error(f"❌ [模块错误] {module_name} - {error}")
```

### Configuration
- Default configuration in `tradingagents/default_config.py` as `DEFAULT_CONFIG` dict
- Environment variables via `.env` file
- User configs loaded from MongoDB or override dict
- Use `os.getenv()` with defaults: `os.getenv("VAR", "default_value")`

### Project Structure
```
tradingagents/
├── __init__.py
├── default_config.py      # Default configuration
├── graph/               # LangGraph implementation
├── agents/              # Agent implementations
├── dataflows/           # Data sources and providers
├── tools/               # Analysis tools
├── llm_adapters/        # LLM provider adapters
├── utils/               # Utilities (logging, stock utils)
└── config/              # Configuration management
```

### Key Patterns
- **Factory functions** for LLM creation: `create_llm_by_provider()`
- **Adapter pattern** for LLM providers: `ChatDeepSeekOpenAI`, `ChatDashScopeOpenAI`
- **State management** using `TypedDict` and `Annotated` for LangGraph
- **Singleton pattern** for loggers and managers
- **Tool nodes** grouped by category: market, social, news, fundamentals

### Language
- Code comments and variable names: English
- User-facing messages (prompts, logs, errors): Chinese (simplified)
- Docstrings: English with Chinese descriptions where appropriate

### Important Notes
- Memory management: Use `FinancialSituationMemory` with proper session IDs
- Stock validation: Use `StockUtils.get_market_info()` for stock type detection
- Tool calling: LLMs may call tools multiple times - handle gracefully
- Database: MongoDB for persistent data, Redis for caching (if configured)
- API Keys: Prefer database config over environment variables for dynamic updates
