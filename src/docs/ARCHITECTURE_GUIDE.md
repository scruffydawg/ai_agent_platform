# GUIDE Architecture (v3.0) - Memory & Capability Retrieval

The **GUIDE (Complete Memory & Capability Architecture)** is the core intelligence layer of the AI Agent Platform. It provides a structured, high-performance, and ADHD-friendly way for agents to manage context and recover from interruptions.

## 1. The 5-Lane Memory Structure

Unlike traditional agents that use a single "chat history" list, GUIDE segregates memory into five distinct functional lanes:

### 🚦 Session Lane
*   **Purpose**: Immediate short-term conversation context.
*   **Behavior**: Contains the last N messages of the current dialogue. Compressed or pruned when reaching token limits.

### 📝 Working Lane
*   **Purpose**: Active task state and goals.
*   **Attributes**: Tracks `current_task`, `step_index`, and specific variables relevant to the current execution node.
*   **Impact**: Ensures the agent remains focused on the objective even if the conversation drifts.

### 🔄 Resume Lane
*   **Purpose**: Interruption recovery (ADHD-friendly).
*   **Behavior**: Automatically populated when a task is halted or a crash is detected. Stores the exact state needed to "Pick up where we left off."
*   **UI**: Triggers the `ResumePanel` in the frontend.

### 📚 Semantic Lane
*   **Purpose**: Long-term knowledge and user preferences.
*   **Retrieval**: Triggered by keyword analysis or explicit knowledge requests.
*   **Content**: "User prefers Python for data tasks," "Server IP is 192.168.1.100," etc.

### 🎬 Episodic Lane
*   **Purpose**: Historical experience.
*   **Behavior**: Stores summaries of past successful task completions and failures to improve future performance.

---

## 2. The Memory Broker Pipeline

The Memory Broker is a specialized service (`src/memory/broker.py`) that orchestrates the assembly of the "Context Packet" for the LLM. It follows an 8-stage pipeline:

1.  **Request Analysis**: Determines which memory lanes are likely relevant to the current prompt.
2.  **Lane Selection**: Dispatches retrieval requests to the identified lanes.
3.  **Candidate Retrieval**: Fetches potential memory fragments from the `MemoryManager`.
4.  **Eligibility Filtering**: Removes sensitive or "blocked" data based on security settings.
5.  **Relevance Ranking**: Scores candidates based on keyword matching, recency, and confidence.
6.  **De-duplication**: Removes redundant information across lanes.
7.  **Budget Policy**: Applies token-based limits, prioritizing "Working" and "Session" lanes.
8.  **Packet Assembly**: Formats the final list of messages (System prompt + Contextual Memories + History) for the LLM.

---

## 3. ADHD-Friendly Features

GUIDE is specifically designed to reduce cognitive load:
*   **Context Transparency**: The **Memory Inspector** allows the user to see exactly *what* the agent remembers during any given step.
*   **State Persistence**: The **Resume Memory** mechanic prevents the "What was I doing?" frustration by preserving task state across restarts.
*   **Focus Guard**: By separating "Working Memory" from "Session Chat," the agent is less likely to be distracted by off-topic user messages.

---

## 4. Implementation Details

*   **Models**: Defined in `src/memory/storage.py` using Pydantic.
*   **Management**: Orchestrated by `MemoryManager` in `src/memory/manager.py`.
*   **Integration**: Seamlessly hooked into `StateGraphOrchestrator` via `assemble_context_packet`.
