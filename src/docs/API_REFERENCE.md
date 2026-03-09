# 📖 V2 API REFERENCE

This document provides a detailed reference for all standardized V2 API endpoints.

## Base URL
`http://[hostname]:8001/api/v2`

## Standard Response Envelope
All successful requests return a `SuccessResponse`:
```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional descriptive text"
}
```

## Endpoints

### 🩺 Health & Monitoring
`GET /health` | `GET /health/ready` | `GET /health/live`
- **Description**: Returns system health status and version info.
- **Success Data**: `{"status": "healthy", "version": "2.0.0-alpha", "uptime": "..."}`

### ⚙️ Configuration
`GET /config/`
- **Description**: Retrieves current runtime settings.
- **Success Data**: `{ "llm": { "model": "...", "base_url": "..." }, "storage": { ... } }`

`POST /config/`
- **Description**: Updates runtime settings.
- **Request Body**: `ConfigUpdate` model.

### 💬 Sessions
`GET /sessions/`
- **Description**: Lists all active chat sessions.
- **Success Data**: List of `SessionInfo` objects.

`GET /sessions/{session_id}`
- **Description**: Retrieves message history for a specific session.

### ⚖️ Approvals
`GET /approvals`
- **Description**: Lists all pending human-in-the-loop task approvals.
- **Success Data**: List of `ApprovalRequest` objects.

### 📚 Knowledge Hub (RAG)
`GET /knowledge/search?q={query}`
- **Description**: performs a vector search against the local knowledge base.
- **Success Data**: List of relevant document chunks with similarity scores.

### ⚒️ SkillForge
`POST /forge/interview`
- **Description**: Triggers the iterative AI skill generation interview.
- **Request Body**: `{"prompt": "...", "current_state": { ... }}`

### 🔧 Tool Registry
`GET /tools/registry`
- **Description**: Standardized list of all Native Skills and MCP Servers.
- **Success Data**: List of `ToolCapability` objects (Enveloped).

### 🚀 Runtime
`POST /chat`
- **Description**: Primary endpoint for agent interaction and graph execution.
- **Request Body**: `{"prompt": "...", "history": []}`
- **Response**: Server-Sent Events (SSE) stream.

## 📡 Event Bus Schema

The platform utilizes a standardized event model for communication between the Runtime and the UI components.

| Event Type | Description | Payload Detail |
|---|---|---|
| `run.started` | Execution instance initialized | `run_id`, `timestamp`, `trigger` |
| `run.planned` | Multi-node strategy generated | `plan_steps`, `depth` |
| `step.started` | Individual node process began | `node_id`, `state_snapshot` |
| `step.completed` | Node processing finished | `output`, `metrics` |
| `tool.requested` | Agent requested external action | `tool_name`, `arguments`, `needs_approval` |
| `approval.requested`| Policy gate blocking execution | `approval_id`, `capability`, `reason` |
| `memory.persisted` | Long-term learning event | `fact`, `relevance_score` |
