#!/usr/bin/env bash
# ─── Link an existing container to the brainerd_net network ──────────────────
# Usage: ./scripts/link_container.sh <container_name_or_id>
#
# After linking, the container can reach Brainerd at:
#   http://brainerd:8000
#   WS: ws://brainerd:8000/chat/ws/<session_id>

set -euo pipefail

CONTAINER="${1:-}"
NETWORK="brainerd_net"

if [[ -z "$CONTAINER" ]]; then
    echo "Usage: $0 <container_name_or_id>"
    exit 1
fi

# Create network if it doesn't exist
docker network create "$NETWORK" 2>/dev/null || true

# Connect the container
docker network connect "$NETWORK" "$CONTAINER"

echo "✓ Container '$CONTAINER' connected to '$NETWORK'"
echo "  Reach Brainerd at: http://brainerd:8000"
echo "  WebSocket chat:    ws://brainerd:8000/chat/ws/<session_id>"
echo "  Docs:              http://brainerd:8000/docs"
