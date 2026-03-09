from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from apps.api.middleware import register_middleware
from apps.api.routes.health_routes import router as health_router
from apps.api.routes.config_routes import router as config_router
from apps.api.routes.session_routes import router as session_router
from apps.api.routes.memory_routes import router as memory_router
from apps.api.routes.vision_routes import router as vision_router
from apps.api.routes.browser_routes import router as browser_router
from apps.api.routes.voice_routes import router as voice_router
from apps.api.routes.swarm_routes import router as swarm_router
from apps.api.routes.knowledge_routes import router as knowledge_router
from apps.api.routes.forge_routes import router as forge_router
from apps.api.routes.runtime_routes import router as runtime_router
from apps.api.routes.approval_routes import router as approval_router
from packages.services.event_service import event_service
from src.utils.logger import logger
import json
import asyncio

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Agent Platform API",
        version="2.0.0-alpha",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_middleware(app)

    # V2 API Router
    from fastapi import APIRouter
    v2_router = APIRouter(prefix="/api/v2")

    # Core Routes (V2)
    v2_router.include_router(health_router, tags=["health"])
    v2_router.include_router(config_router, prefix="/config", tags=["config"])
    v2_router.include_router(session_router, prefix="/sessions", tags=["sessions"])
    v2_router.include_router(memory_router, prefix="/memory", tags=["memory"])
    v2_router.include_router(vision_router, prefix="/vision", tags=["vision"])
    v2_router.include_router(browser_router, prefix="/browser", tags=["browser"])
    v2_router.include_router(voice_router, prefix="/voice", tags=["voice"])
    v2_router.include_router(swarm_router, prefix="/swarm", tags=["swarm"])
    v2_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
    v2_router.include_router(forge_router, prefix="/forge", tags=["forge"])
    v2_router.include_router(runtime_router, prefix="/runtime", tags=["runtime"])
    v2_router.include_router(approval_router, prefix="/approvals", tags=["approvals"])

    # Include Tool Registry from src.routers
    from src.routers.tools import router as tools_router
    v2_router.include_router(tools_router, tags=["tools"])

    app.include_router(v2_router)

    # Compatibility Aliases (V1 -> V2) - Root level
    app.include_router(health_router, tags=["legacy"])
    app.include_router(swarm_router, prefix="/swarm", tags=["legacy"])
    
    @app.post("/chat", tags=["legacy"])
    async def legacy_chat(request: Request):
        from apps.api.routes.runtime_routes import chat
        return await chat(await request.json()) # Simplification, better to call service directly
    
    @app.post("/run", tags=["legacy"])
    async def legacy_run(request: Request):
        from apps.api.routes.runtime_routes import run_graph
        from apps.api.routes.runtime_routes import RunRequest
        body = await request.json()
        return await run_graph(RunRequest(**body))

    # ... and so on for other critical UI endpoints
    async def root() -> dict:
        return {
            "name": "AI Agent Platform API",
            "version": "2.0.0-alpha",
            "status": "active",
            "architecture": "modular"
        }

    @app.websocket("/stream")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        
        # Subscribe to EventBus
        async def on_event(event):
            try:
                await websocket.send_text(json.dumps(event))
            except Exception:
                # If sending fails, we should probably stop the subscription
                pass
            
        event_service.subscribe(on_event)
        
        try:
            # Send initial heartbeat
            await websocket.send_text(json.dumps({"type": "heartbeat", "status": "connected"}))
            while True:
                await websocket.receive_text() # Keep alive
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        finally:
            event_service.unsubscribe(on_event)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
