# 🧪 Alchemy Crafter

**A single-player alchemy discovery game powered by a local LLM.**  
Combine elements to discover new ones — **infinitely**.

```text
fire + water → steam
steam + earth → mud
mud + fire → ash
...
```

Results are **AI-generated** on first discovery (via Ollama) and then **cached permanently**. Every session builds on the last, creating your own evolving elemental world.

---

## ✨ Highlights

- **Infinite crafting** — no hardcoded recipes; fresh discoveries powered by local LLM
- **Blazing fast** on repeats thanks to Redis cache (< 50ms)
- **Persistent world** stored in PostgreSQL
- **Local-first** — runs entirely on your machine with Docker Compose + Ollama
- **CLI + API** — interactive game loop or HTTP endpoints (Swagger included)
- **Strict validation** — clean, single-word substance elements only

Inspired by Little Alchemy, but with AI-driven infinite possibilities.

---

## 🏗️ Architecture

```mermaid
graph TD
    Client["Client<br/>(CLI or API)"]
    Redis["Redis<br/>⚡ &lt;50ms"]
    Postgres["PostgreSQL<br/>📦 &lt;150ms"]
    Ollama["Ollama (LLM)<br/>🤖 &lt;2s"]

    Client -->|"1. validate + normalise"| Redis
    Redis -->|"2. cache miss"| Postgres
    Postgres -->|"3. db miss"| Ollama
    Ollama -->|"4. validate result"| Postgres
    Postgres -->|"5. persist"| Redis
    Redis -->|"6. return"| Client

    style Redis fill:#e63946,color:#fff
    style Postgres fill:#2b6cb0,color:#fff
    style Ollama fill:#6b46c1,color:#fff
```

**Core principles**: Cache-first, never trust raw LLM output, order-independent combinations (`fire + water` == `water + fire`), and silent degradation on cache/DB issues.

---

## 🔄 Combine Pipeline

```mermaid
flowchart TD
    A([POST /combine]) --> B{Same element?}
    B -->|yes| C[422 Unprocessable]
    B -->|no| D{Both elements discovered?}
    D -->|no| E[404 Unknown element]
    D -->|yes| F{Redis cache hit?}
    F -->|hit| G[Return cached]
    F -->|miss| H{Postgres hit?}
    H -->|hit| I[Cache + return]
    H -->|miss| J[Acquire lock<br/>API only]
    J --> K[Call Ollama\nwith retries]
    K --> L{Valid single-word result?}
    L -->|no| K
    L -->|yes| M[Save to Postgres + Redis]
    M --> N[Return\nis_new: true]
```

---

## 🐳 Services (Docker Compose)

```mermaid
graph LR
    subgraph "Docker Compose"
        S["🖥️ server :8000"]
        P["🐘 postgres :5432"]
        R["⚡ redis :6379"]
        O["🤖 ollama :11434"]
        A["🗄️ adminer :8080"]
        RI["📊 redisinsight :5540"]
    end

    S --> P
    S --> R
    S --> O
```

---

## 📁 Project Structure

```text
alchemy-crafter/
├── src/
│   ├── config.py
│   ├── logger.py
│   ├── combine.py           ← core pipeline
│   ├── validation.py
│   ├── db/
│   ├── cache/
│   ├── ai/
│   ├── api/
│   └── game/
├── tests/                   ← unit + integration tests
├── docker-compose.yml
├── Dockerfile.server
├── Makefile
├── pyproject.toml           ← uv + dependencies
└── .env.example
```

*(Generated tree: [docs/STRUCTURE.md](docs/STRUCTURE.md))*

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/KarthikUdyawar/alchemy-crafter
cd alchemy-crafter
```

### 2. Copy environment config

```bash
cp .env.example .env
```

### 3. Start services

```bash
make setup    # first-time setup
make up       # docker compose up
```

### 4. Pull the LLM model

```bash
make pull-model                     # defaults to llama3
# or
make pull-model OLLAMA_MODEL=mistral
```

### 5. Play the game

```bash
make dev      # CLI interactive mode
```

### 6. Or run the API

```bash
make serve          # development (hot reload)
make serve-prod     # production (4 workers)
```

**API docs** will be available at `http://localhost:8000/docs`

---

## ⚙️ Configuration (`.env`)

| Variable         | Default                                               | Description                    |
| ---------------- | ----------------------------------------------------- | ------------------------------ |
| `DATABASE_URL`   | `postgresql://alchemy:alchemy@localhost:5432/alchemy` | Postgres connection            |
| `REDIS_URL`      | `redis://localhost:6379/0`                            | Redis connection               |
| `OLLAMA_URL`     | `http://localhost:11434`                              | Ollama endpoint                |
| `OLLAMA_MODEL`   | `llama3`                                              | Model name                     |
| `OLLAMA_TIMEOUT` | `100`                                                 | Timeout in seconds             |
| `CACHE_TTL`      | `86400`                                               | Redis cache TTL (seconds)      |
| `CONTEXT_SIZE`   | `10`                                                  | Recent elements for AI prompt  |
| `LOG_LEVEL`      | `WARNING`                                             | DEBUG / INFO / WARNING / ERROR |

---

## 🌐 API Reference

**Base URL:** `http://localhost:8000`

| Method | Endpoint    | Description             |
| ------ | ----------- | ----------------------- |
| `GET`  | `/health`   | Liveness probe          |
| `POST` | `/combine`  | Combine two elements    |
| `GET`  | `/elements` | List all known elements |
| `GET`  | `/recipes`  | List all known recipes  |

**Example** (`POST /combine`):

```json
// Request
{"a": "fire", "b": "water"}

// Response
{
  "result": "steam",
  "is_new": true,
  "source": "ai",
  "elapsed_ms": 1220
}
```

`source` can be `cache`, `db`, or `ai`.

---

## 🎮 CLI Commands

- `fire water` or `combine fire water` → combine elements
- `list` → show all discovered elements
- `stats` → session statistics & milestones
- `help` → command reference
- `quit` / `exit` → session summary

---

## 🏆 Milestones

```mermaid
graph LR
    A["🌱 Apprentice (10)"] --> B["⚗️ Journeyman (25)"]
    B --> C["🔥 Expert (50)"]
    C --> D["🌟 Master (100)"]
    D --> E["🧙 Grand Alchemist (200)"]
```

---

## 🛠️ Makefile Reference

| Command            | Description                                |
| ------------------ | ------------------------------------------ |
| `make setup`       | First-time setup                           |
| `make up` / `down` | Start/stop Docker services                 |
| `make dev`         | Run CLI game                               |
| `make serve`       | API dev server (hot-reload)                |
| `make serve-prod`  | API production (4 workers)                 |
| `make test`        | Unit tests (offline)                       |
| `make test-all`    | All tests (requires `make up`)             |
| `make lint`        | Pre-commit hooks except mypy (fixes files) |
| `make typecheck`   | Strict mypy                                |
| `make check`       | lint + typecheck + test                    |
| `make ci`          | Run the CI job locally (needs `act`)       |
| `make tree`        | Regenerate `docs/STRUCTURE.md`             |
| `make status`      | Branch, stashes, recent commits            |
| `make pull-model`  | Download Ollama model                      |
| `make clear-all`   | Reset Redis + DB                           |
| `make nuke`        | Stop + wipe all volumes                    |

---

## 🧪 Testing

- `make test` — offline unit tests, fast
- `make test-all` — includes integration tests (run `make up` first)

Markers: `@pytest.mark.unit` | `@pytest.mark.integration`

---

## 📊 Monitoring & Tools

- **Adminer** (Postgres): `http://localhost:8080`
- **RedisInsight**: `http://localhost:5540`
- **Swagger**: `http://localhost:8000/docs`

Default credentials are in the project (see `docker-compose.yml`).

---

## 🗄️ Data Model

**PostgreSQL** — `elements` and `recipes` tables with proper constraints.  
**Redis** keys: `recipe:<a>:<b>`, `context:global`, `lock:<a>:<b>`, etc.

*(Detailed ER diagram and key descriptions in `ARCHITECTURE.md`)*

---

## 🔮 Roadmap

- **V1 (Done)**: CLI + API + core pipeline + Docker
- **V2**: Web UI (HTMX/React), player accounts, discovery graph
- **V3**: Achievements, hints, rarity tiers, daily challenges
- **V4**: Multiplayer discovery race, AI lore generation

---

## 🧠 Development Notes

- Inputs are always **normalized and sorted** alphabetically.
- LLM output is **strictly validated** (single lowercase word, substance-like).
- Cache and DB failures are non-fatal — gameplay continues.
- Use `LOG_LEVEL=DEBUG` for full pipeline visibility.

See `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, and `docs/sprints/` for deeper details.

---

**Last updated:** May 2026  
**Status:** Core MVP complete (Sprint 1 ✅)

---

## Contributing

Pull requests welcome! Please run `make check` and ensure new code follows the validation + logging patterns.

---

**Made with ❤️ for tinkerers who love discovery, local AI, and clean architecture.**
