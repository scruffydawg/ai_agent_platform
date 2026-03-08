import asyncio
from pathlib import Path
from src.memory.knowledge_base import kb_manager
from src.utils.logger import logger

async def seed_system_knowledge():
    """
    Reads the project's documentation and expert souls, 
    vectorizes them, and stores them in Qdrant via the KnowledgeBaseManager.
    """
    logger.info("Starting system knowledge seeding (RAG v2)...")
    
    docs_to_index = [
        "src/agents/experts/Observer.md",
        "src/agents/experts/Researcher.md",
        "src/agents/experts/Analyst.md",
        "src/agents/experts/Architect.md",
        "src/agents/experts/Security.md",
        "src/agents/experts/ADHD_UX.md"
    ]
    
    project_root = Path("/home/scruffydawg/gemini_workspace/ai_agent_platform")
    
    for doc_path in docs_to_index:
        abs_path = project_root / doc_path
        if not abs_path.exists():
            logger.warning(f"Doc not found: {abs_path}")
            continue
            
        logger.info(f"Ingesting: {doc_path}")
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        metadata = {
            "source": doc_path,
            "filename": doc_path.split("/")[-1],
            "category": "system_documentation"
        }
        
        await kb_manager.ingest_document(content, metadata)

    logger.info("System knowledge seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_system_knowledge())
