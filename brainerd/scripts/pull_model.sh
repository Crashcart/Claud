#!/usr/bin/env bash
# ─── Pull or swap Ollama model ────────────────────────────────────────────────
# Usage: ./scripts/pull_model.sh [model_name]
# Default: mistral:7b
#
# Other good choices for low-CPU systems:
#   phi3:mini          (~2.3 GB, very fast, less creative)
#   mistral:7b-q4_K_M  (~4.1 GB, best quality/speed for this hardware)
#   llama3.2:3b        (~2.0 GB, good reasoning)

set -euo pipefail

MODEL="${1:-mistral:7b}"

echo "Pulling model: $MODEL"
docker exec brainerd_ollama ollama pull "$MODEL"

echo ""
echo "To use this model, set OLLAMA_MODEL=$MODEL in your .env file and restart brainerd."
