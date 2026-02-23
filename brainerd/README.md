# Brainerd AI

Local-first AI hub built on **Ollama** (`mistral:7b`) with optional **Google Gemini** fallback. Runs as a Docker container and exposes a REST + WebSocket API for other containers to consume.

## Features

- **Chat** — REST and WebSocket endpoints with persistent session history
- **RPG Engine** — Multi-world game master (fantasy, sci-fi, horror, western, custom)
- **Dual AI backend** — Ollama (local, always-on) + Google Gemini (optional, set API key)
- **SQLite database** — Zero-config, disk-heavy storage with full chat/game history
- **Docker networking** — Other containers join `brainerd_net` and call `http://brainerd:8000`

## Quick Start

```bash
cp .env.example .env
# Edit .env if you want Google AI (set GOOGLE_AI_API_KEY)

docker compose up -d
# First run pulls mistral:7b (~4 GB) — this is a one-time download
```

API docs: http://localhost:8000/docs

## Model Choice

**`mistral:7b`** (default) — best for creative RPG narration and chat on low-CPU hardware.

Alternatives (swap via `OLLAMA_MODEL` in `.env`):
| Model | Size | Best for |
|---|---|---|
| `mistral:7b` | ~4 GB | Chat + RPG (default) |
| `phi3:mini` | ~2.3 GB | Fast responses, low RAM |
| `llama3.2:3b` | ~2 GB | Reasoning tasks |

## Inter-Container Communication

Any Docker container can link to Brainerd:

```bash
# One-time network join
./scripts/link_container.sh my-other-container

# Then inside that container:
curl http://brainerd:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Or add to `docker-compose.yml`:
```yaml
networks:
  brainerd_net:
    external: true
```

## API Reference

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/chat/` | Send message, get response |
| GET | `/chat/sessions` | List chat sessions |
| GET | `/chat/sessions/{id}/messages` | Get message history |
| WS | `/chat/ws/{session_id}` | Streaming WebSocket chat |

### RPG

| Method | Path | Description |
|---|---|---|
| POST | `/rpg/games` | Create new game |
| GET | `/rpg/games` | List games |
| POST | `/rpg/games/{id}/action` | Take action, get narration |
| GET | `/rpg/games/{id}/turns` | Get full turn history |

### WebSocket Protocol

Send:
```json
{"message": "I look around the tavern", "provider": "auto"}
```

Receive (streamed):
```json
{"type": "chunk", "content": "The tavern is dimly lit..."}
{"type": "done", "session_id": "...", "message_id": "..."}
```
