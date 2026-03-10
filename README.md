# 🧠 AI Agent Platform

A self-hosted, LAN-accessible, ADHD-optimized AI Agent Platform and Orchestration Engine built from scratch.

> **"THE FLUTE PATH IS CLEAR."** 

## 🚀 Key Features

*   **GUIDE Architecture v3.0:** A complete memory and capability system featuring a 5-lane memory structure (Session, Working, Resume, Semantic, Episodic) and an 8-stage intelligent Memory Broker retrieval pipeline.
*   **Multi-Agent Orchestration:** Driven by the `StateGraphOrchestrator` with full async support and a Swarm of expert personas (Architect, ADHD_UX, Security, etc.).
*   **ADHD-Optimized Recovery:** Features a "Resume Memory" lane for automatic interruption recovery and a "Memory Inspector" for transparent context assembly.
*   **The "Ouch" Mechanic (Self-Healing):** Native tool-level exception catching, Circuit Breakers, and automated LLM-feedback loops for autonomous error recovery.
*   **Three-Pillar Tool Registry:** A unified structure for Native Skills, MCP Servers, and Code Tools with integrated **Contextual Consult**.
*   **SkillForge Wizard:** An AI-powered, back-and-forth interview wizard to help users generate "Skills on Steroids" (standardized Google-style docstrings, usage examples, and automatic Deep Recon discovery for MCP packages).
*   **Dynamic Visual UI:** A tabbed, responsive React dashboard featuring real-time terminal streams, node telemetry, visual logic graphs, and interactive capability cards.
*   **Tailscale & LAN Ready:** Fully responsive design (using `dvh` units for mobile/iPad) with dynamic API routing out of the box.

## 📖 Documentation

For a comprehensive breakdown of the architecture, features, and capabilities, please refer to the main documentation:

👉 **[Platform Overview & Architecture (src/docs/PLATFORM_OVERVIEW.md)](src/docs/PLATFORM_OVERVIEW.md)**
👉 **[V2 API Architecture (src/docs/ARCHITECTURE_V2.md)](src/docs/ARCHITECTURE_V2.md)**
👉 **[V2 Migration Guide (src/docs/MIGRATION_GUIDE.md)](src/docs/MIGRATION_GUIDE.md)**

---

## 🛠️ Quick Start

1.  **Create your environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up configuration:**
    ```bash
    cp .env.example .env
    # Edit .env with your required API keys (e.g., OPENAI_API_KEY, AGENT_API_KEY)
    ```
4.  **Run the Backend (FastAPI):**
    ```bash
    uvicorn apps.api.app:app --host 0.0.0.0 --port 8001
    ```
5.  **Run the Frontend (React/Vite):**
    ```bash
    cd frontend
    npm install
    npm run dev -- --host 0.0.0.0
    ```
