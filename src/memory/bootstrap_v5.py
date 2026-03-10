import asyncio
import json
from pathlib import Path
from src.memory.db_engine import init_db, AsyncSessionLocal, MemoryEntryModel, AgentMemoryModel
from src.memory.vector_engine import VectorEngine
from src.memory.storage import AgentMemory, MemoryEntry, MemoryLane
from src.config import MEMORY_DIR
from apps.api.settings import get_settings

async def bootstrap():
    print("🚀 Initializing GUIDE v5 Databases...")
    
    # 1. Init Postgres
    await init_db()
    print("✅ Postgres tables created.")

    # 2. Init Qdrant
    vec = VectorEngine()
    await vec.init_collections()
    print("✅ Qdrant collections initialized.")

    # 3. Migrate Legacy Files
    print("📂 Checking for legacy memory files...")
    legacy_files = list(MEMORY_DIR.glob("*_memory.json"))
    
    if not legacy_files:
        print("ℹ️ No legacy files found.")
        return

    async with AsyncSessionLocal() as session:
        for f in legacy_files:
            agent_id = f.name.replace("_memory.json", "")
            print(f"📦 Migrating {agent_id}...")
            
            with open(f, "r") as file:
                data = json.load(file)
            
            # Simple migration to DB
            async with session.begin():
                # Add Agent
                db_agent = AgentMemoryModel(
                    agent_id=agent_id,
                    system_prompt=data.get("system_prompt", ""),
                    task_status=data.get("task_status", "idle")
                )
                session.add(db_agent)
                
                # Add Entries
                for lane_name in ["session", "working", "semantic", "episodic"]:
                    items = data.get(lane_name, [])
                    for item in items:
                        db_entry = MemoryEntryModel(
                            agent_id=agent_id,
                            role=item.get("role", "user"),
                            content=item.get("content", ""),
                            lane=lane_name,
                            source=item.get("source", "legacy"),
                            confidence=item.get("confidence", 1.0),
                            provenance=item.get("provenance", {}),
                            meta_data=item.get("metadata", {})
                        )
                        session.add(db_entry)
            print(f"✅ Migrated {agent_id}")

    print("🏁 Bootstrap and Migration Complete!")

if __name__ == "__main__":
    asyncio.run(bootstrap())
