# AI Agent Platform: V2 Architecture

This document describes the standardized V2 API architecture introduced in Phase 12.

## Overview

The V2 API is designed for modularity, scalability, and ease of integration. All V2 endpoints are prefixed with `/api/v2` and follow a consistent response format.

## Core Principles

1.  **Prefixing**: All V2 routes are under `/api/v2`.
2.  **Standardized Responses**: All successful responses follow the `SuccessResponse` model:
    ```json
    {
      "status": "success",
      "data": { ... },
      "message": "Optional message"
    }
    ```
3.  **Error Handling**: Consistent `ErrorResponse` model with specific codes and detail dictionaries.
4.  **Tagging**: Routes are logically grouped using FastAPI tags (e.g., `health`, `config`, `tools`, `forge`).

## Endpoint Groups

### Core Services
-   `/api/v2/health`: System health and versioning.
-   `/api/v2/config`: Application settings and runtime configuration.
-   `/api/v2/sessions`: Multi-agent session management and history.
-   `/api/v2/approvals`: Human-in-the-loop task approval workflow.

### Advanced Capabilities
-   `/api/v2/tools`: Unified Tool Registry (Skills + MCP Servers).
-   `/api/v2/knowledge`: RAG-based knowledge retrieval and ingestion.
-   `/api/v2/forge`: Automated skill creation and iterative prompt engineering.
-   `/api/v2/runtime`: Execution engine for agent graphs and chat.

### Media & Interfaces
-   `/api/v2/vision`: Image analysis and OCR.
-   `/api/v2/voice`: STT and TTS services.
-   `/api/v2/browser`: Autonomous web navigation and data extraction.
-   `/api/v2/swarm`: Swarm telemetry and inter-agent communication.

## Core System Services

To ensure modular evolution, the platform is organized around these canonical services:

- **SessionService**: Manages chat history and state hydration.
- **MemoryService**: Handles long-term fact storage and pattern recognition.
- **ApprovalService**: Manages human-in-the-loop policy gates.
- **ConfigService**: Handles environment and runtime parameter security.
- **SkillRegistryService**: Discovers and indexes available capabilities.
- **RuntimeService**: Orchestrates the multi-agent graph execution.
- **EventService**: Provides the underlying Pub/Sub event bus for UI and inter-service sync.

## Implementation Detail

The V2 router is defined in `apps/api/app.py` as a master `APIRouter` that includes individual sub-routers from `apps/api/routes/` and `src/routers/`.

```python
v2_router = APIRouter(prefix="/api/v2")
v2_router.include_router(health_router, tags=["health"])
v2_router.include_router(tools_router, tags=["tools"])
# ...
app.include_router(v2_router)
```

## Backward Compatibility

Legacy V1 routes (e.g., `/chat`, `/run`, `/swarm/*`) are maintained at the root level as aliases to their V2 counterparts to prevent breaking existing UI integrations during the transition.
