import os
from pathlib import Path
from src.skills.vector_memory import vector_memory
from src.utils.logger import logger

def seed_system_knowledge():
    """
    Reads the project's documentation and expert souls, 
    vectorizes them, and stores them in Qdrant.
    This gives the 'Guide' LLM self-awareness of its own build.
    """
    logger.info("Starting system knowledge seeding...")
    
    docs_to_index = [
        "/home/scruffydawg/.gemini/antigravity/brain/5ebdc081-4d10-42e6-828d-566a4a13c6ac/implementation_plan.md",
        "/home/scruffydawg/.gemini/antigravity/brain/5ebdc081-4d10-42e6-828d-566a4a13c6ac/walkthrough.md",
        "src/agents/experts/Observer.md",
        "src/agents/experts/Researcher.md",
        "src/agents/experts/Analyst.md",
        "src/agents/experts/Architect.md",
        "src/agents/experts/Security.md",
        "src/agents/experts/ADHD_UX.md"
    ]
    
    ids = []
    texts = []
    payloads = []
    
    project_root = Path("/home/scruffydawg/gemini_workspace/ai_agent_platform")
    
    for doc_path in docs_to_index:
        p = Path(doc_path)
        if not p.is_absolute():
            abs_path = project_root / doc_path
        else:
            abs_path = p
            
        if not abs_path.exists():
            logger.warning(f"Doc not found: {abs_path}")
            continue
            
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Display name for payload
        display_name = doc_path.split("/")[-1]
        chunks = content.split("\n\n")
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue
                
            chunk_id = f"{doc_path.replace('/', '_')}_{i}"
            ids.append(chunk_id)
            texts.append(chunk)
            payloads.append({
                "source": display_name,
                "type": "system_documentation",
                "chunk": i
            })
            
    if texts:
        logger.info(f"Indexing {len(texts)} chunks into Qdrant...")
        vector_memory.upsert(ids, texts, payloads)
        logger.info("System knowledge seeding complete.")
    else:
        logger.error("No documentation found to index.")

if __name__ == "__main__":
    seed_system_knowledge()
