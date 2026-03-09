# V2 Migration Guide

This guide assists in migrating from the legacy V1 API to the standardized V2 architecture.

## Key Changes

### 1. Base URL Update
The most significant change is the introduction of the `/api/v2` prefix.

-   **Old**: `http://localhost:8001/health`
-   **New**: `http://localhost:8001/api/v2/health`

### 2. Standardized Response Envelopes
All V2 endpoints now wrap their results in a `SuccessResponse` object.

**V1 Response (Example):**
```json
[
  {"name": "Skill A", "status": "Active"},
  {"name": "Skill B", "status": "Active"}
]
```

**V2 Response (Example):**
```json
{
  "status": "success",
  "data": [
    {"name": "Skill A", "status": "Active"},
    {"name": "Skill B", "status": "Active"}
  ],
  "message": "Registry loaded successfully"
}
```

### 3. Path Normalization
Some paths have been normalized for consistency:

| Service | V1 Path (Legacy) | V2 Path (Standardized) |
| :--- | :--- | :--- |
| Config | `/config/settings` | `/api/v2/config/` |
| Sessions | `/sessions/active` | `/api/v2/sessions/` |
| Knowledge | `/knowledge/search` (POST) | `/api/v2/knowledge/search` (GET + query param) |
| Tool Registry | `/tools/registry` (Flat) | `/api/v2/tools/registry` (Enveloped) |

## Migration Steps for Frontend

1.  **Update API Client**: Adjust the `baseURL` for your API service instance to point to `/api/v2`.
2.  **Update Response Parsing**: Access the actual data through the `data` property of the response object.
3.  **Handle Status Codes**: V2 relies more strictly on HTTP status codes (404 for missing items, 405 for wrong methods) instead of custom error messages inside 200 responses.

## Compatibility Layer
A compatibility layer exists at the root level of `app.py` to support legacy `/chat` and `/run` calls. However, these will be deprecated in future phases.
