#!/bin/bash
# High-performance llama-server startup script for GLM-4.7-Flash
PROJECT_ROOT="/home/scruffydawg/gemini_workspace/ai_agent_platform"
LLAMA_SERVER_BIN="/home/scruffydawg/gemini_workspace/llama.cpp/build/bin/llama-server"
MODEL_PATH="$PROJECT_ROOT/models/glm-4.7-flash/Huihui-GLM-4.7-Flash-abliterated.Q4_K_M.gguf"

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Error: Model not found at $MODEL_PATH"
    exit 1
fi

echo "🚀 Launching llama-server on port 8081 (CPU-only mode)..."
echo "Config: 16k Context, Multi-threaded CPU optimized"

$LLAMA_SERVER_BIN \
  -m "$MODEL_PATH" \
  --port 8081 \
  --ctx-size 16384 \
  --n-gpu-layers 0 \
  --threads $(nproc) \
  --parallel 1 \
  --cont-batching

