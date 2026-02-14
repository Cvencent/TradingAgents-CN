# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingAgents-CN is a Chinese-enhanced multi-agent AI stock analysis platform built on LangGraph. It combines LLM-powered agent orchestration with financial data analysis for A-shares, Hong Kong, and US stock markets. The project is designed for research and education, not real trading.

**Architecture**: FastAPI backend + Vue 3 frontend + MongoDB/Redis + LangGraph multi-agent system

## Common Commands

### Backend Development

```bash
# Install dependencies
pip install -e .
# or with uv
uv pip install -e .

# Run backend server
python app/main.py
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run tests (from project root)
pytest
# Run specific test
pytest tests/test_analysis.py
# Run integration tests (skipped by default)
pytest -m integration
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## High-Level Architecture

### 1. Multi-Agent Orchestration (LangGraph)

The core of the system is a **LangGraph-based state machine** that orchestrates multiple specialized agents:

**Agent Types**:
- **Analysts**: Market (technical), Fundamentals, News, Social Media, Capital Flow, Market Trend
- **Researchers**: Bull (bullish perspective) and Bear (bearish perspective)
- **Risk Managers**: Aggressive, Conservative, Neutral debators
- **Managers**: Research Manager (coordinates analysts), Risk Manager (coordinates risk debate)
- **Trader**: Final decision maker

**Key Files**:
- `tradingagents/graph/trading_graph.py` - LLM factory and graph creation
- `tradingagents/graph/setup.py` - Graph configuration and node setup
- `tradingagents/graph/conditional_logic.py` - Routing logic between agents
- `tradingagents/agents/` - Individual agent implementations

**State Management**: Uses TypedDict-based state (`AgentState`) with LangChain messages for agent communication.

### 2. Layered Architecture

```
Frontend (Vue 3 + Element Plus)
    ↓
FastAPI Backend (app/)
    ├─ Routers: API endpoints
    ├─ Services: Business logic
    ├─ Middleware: Auth, logging, rate limiting
    └─ Core: Config, database, Redis
    ↓
TradingAgents Core (tradingagents/)
    ├─ Graph: Agent orchestration
    ├─ Agents: Analyst implementations
    ├─ Tools: Technical/fundamental analysis
    ├─ Dataflows: Data providers
    └─ LLM Adapters: Multi-provider support
    ↓
Data Layer (MongoDB + Redis + External APIs)
```

### 3. LLM Provider Abstraction

The system supports multiple LLM providers through a factory pattern:

**Function**: `create_llm_by_provider()` in `tradingagents/graph/trading_graph.py`

**Supported Providers**:
- OpenAI (including compatible endpoints)
- Google Generative AI
- DeepSeek
- Alibaba DashScope
- Anthropic

**Configuration**: LLM settings are stored in MongoDB (`llm_configs` collection) and can be managed via the web UI.

### 4. Data Provider System

**Multi-source fallback strategy** for financial data:

**China Market**:
- Tushare (primary)
- AKShare (fallback)
- BaoStock (fallback)

**Hong Kong/US Markets**:
- YFinance
- Alpha Vantage
- Finnhub

**Location**: `tradingagents/dataflows/providers/`

**Caching**: Multi-level caching (file → MongoDB → Redis) for performance optimization.

### 5. Configuration Management

**Unified config system** with multiple layers:
1. Environment variables (`.env` file)
2. Pydantic Settings (`app/core/config.py`)
3. Database configuration (MongoDB `user_configs` collection)
4. Web UI configuration interface

**Config Bridge**: `app/services/config_service.py` converts web UI settings to environment variables for the core library.

**Dynamic Updates**: Configuration changes take effect without restart.

## Key Workflows

### Stock Analysis Flow

1. User initiates analysis → `POST /api/analysis/analyze`
2. `app/services/analysis_service.py` creates agent graph instance
3. Graph execution:
   - Research Manager calls analysts (market, fundamentals, news, social)
   - Bull & Bear researchers synthesize perspectives
   - Risk Manager debates risk levels
   - Trader makes final decision
4. Results stored in MongoDB
5. Report generated and returned

### Data Synchronization

1. APScheduler triggers sync tasks (configured via CRON expressions)
2. Multi-source sync service attempts providers in priority order
3. Data stored in MongoDB collections
4. Cache invalidated for updated data
5. Status logged for monitoring

**Sync Services**:
- `app/worker/tushare_sync_service.py`
- `app/worker/akshare_sync_service.py`
- `app/worker/baostock_sync_service.py`

## Important Directories

### Backend (`app/`)

- `routers/` - API endpoints (analysis, config, screening, queue, reports, etc.)
- `services/` - Business logic (analysis orchestration, config management, data sync)
- `core/` - Core infrastructure (config, database, Redis, logging)
- `middleware/` - Request processing (auth, logging, rate limiting)
- `worker/` - Background tasks (data synchronization)

### Core Library (`tradingagents/`)

- `graph/` - LangGraph orchestration logic
- `agents/` - Agent implementations (analysts, researchers, managers)
- `tools/` - Analysis tools (technical indicators, news retrieval)
- `dataflows/` - Data providers and caching
- `llm_adapters/` - LLM provider integrations
- `utils/` - Utilities (logging, stock validation, news filtering)

### Frontend (`frontend/`)

- `src/views/` - Page components
- `src/components/` - Reusable UI components
- `src/stores/` - Pinia state management
- `src/api/` - API client functions
- `src/router/` - Vue Router configuration

## Database Collections (MongoDB)

- `stocks` - Stock metadata
- `analysis_results` - Analysis reports
- `user_configs` - User preferences
- `llm_configs` - LLM provider settings
- `data_source_configs` - Data source settings
- `operation_logs` - API operation audit trail
- `token_usage` - LLM token consumption tracking

## Code Style

- Python 3.10+ with type hints
- 4-space indentation
- English code comments, Chinese user-facing messages
- Docstrings with Args/Returns sections
- Async-first approach (FastAPI + Motor)

## Testing

Tests are Python scripts in `tests/` directory. The project uses pytest with custom configuration:

- Default: Skips integration tests
- Run all tests: `pytest`
- Run integration tests: `pytest -m integration`
- Configuration: `tests/pytest.ini`

## Environment Setup

Required environment variables (`.env` file):

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=tradingagents

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM Provider (at least one required)
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
DEEPSEEK_API_KEY=your_key

# Data Sources (at least one required)
TUSHARE_TOKEN=your_token
```

## Key Design Patterns

1. **Factory Pattern**: LLM provider creation
2. **Strategy Pattern**: Data provider selection with fallback
3. **State Machine**: LangGraph-based agent orchestration
4. **Repository Pattern**: Database operations abstraction
5. **Middleware Chain**: Request processing pipeline
6. **Observer Pattern**: SSE/WebSocket for real-time updates

## Important Notes

- **Separation of Concerns**: Core library (`tradingagents/`) is independent from web layer (`app/`)
- **Modular Agents**: Each analyst can be enabled/disabled independently
- **Graceful Degradation**: Falls back to alternative data sources if primary fails
- **Configuration-Driven**: Minimal hardcoding, everything configurable
- **Unified Logging**: All components use centralized logging system
- **Multi-level Caching**: File → MongoDB → Redis for performance

## License

Mixed licensing model:
- **Open Source (Apache 2.0)**: Core library (`tradingagents/`)
- **Proprietary**: Web layer (`app/` and `frontend/`) - requires commercial license for commercial use

## Recent Development Focus

Based on git status, active development areas:
- Agent implementations (analysts, researchers, managers)
- Analysis services and report generation
- Risk management logic
- Graph orchestration improvements
