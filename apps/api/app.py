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
from packages.runtime.orchestration.event_bus import event_bus
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

    # Core Routes
    app.include_router(health_router, tags=["health"])
    app.include_router(config_router, prefix="/config", tags=["config"])
    app.include_router(session_router, prefix="/sessions", tags=["sessions"])
    app.include_router(memory_router, prefix="/memory", tags=["memory"])
    app.include_router(vision_router, prefix="/vision", tags=["vision"])
    app.include_router(browser_router, prefix="/browser", tags=["browser"])
    app.include_router(voice_router, prefix="/voice", tags=["voice"])
    app.include_router(swarm_router, prefix="/swarm", tags=["swarm"])
    app.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
    app.include_router(forge_router, prefix="/forge", tags=["forge"])
    app.include_router(runtime_router, prefix="/runtime", tags=["runtime"])

    # Compatibility Aliases (V1 -> V2)
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
            await websocket.send_text(json.dumps(event))
            
        event_bus.subscribe(on_event)
        
        try:
            # Send initial heartbeat
            await websocket.send_text(json.dumps({"type": "heartbeat", "status": "connected"}))
            while True:
                await websocket.receive_text() # Keep alive
        except WebSocketDisconnect:
            # In a real app, we'd unsubscribe
            pass

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
