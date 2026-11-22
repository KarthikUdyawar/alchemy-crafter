# Alchemy Crafter — Sprint 1: TODO

Scope: [PRD.md](PRD.md). Decisions: [DECISION.md](../../DECISION.md).

## Backlog

### 🏗️ INFRA-1 — Project Setup & Tooling

**Branch:** `feature/project-setup`

- [x] Initialize project with `uv`, create `main.py`, and set up virtual environment
- [x] Install core dependencies (`psycopg2-binary`, `redis`, `httpx`, `python-dotenv`)
- [x] Create `.env.example` and `src/config.py` for loading DB URL, Redis URL, Ollama endpoint, timeout, and log level
- [x] Set up `docker-compose.yml` with Postgres, Redis, and Ollama (including healthchecks)
- [x] Create `Makefile` with targets: `setup`, `up`, `down`, `dev`, `test`, `pull-model`, `db-shell`, `redis-shell`, `nuke`

### 🗄️ DB-1 — PostgreSQL Database Layer

**Branch:** `feature/database`

- [x] Implement `src/db/connection.py` with `get_connection()` (retry logic) and `init_db()`
- [x] Build `src/db/queries.py` with helpers: `get_recipe`, `save_recipe`, `save_element`, `element_exists`, `get_all_elements`, `get_all_recipes`
- [x] Create tables `elements` and `recipes` with proper constraints and indexes
- [x] Seed base elements (fire, water, earth, air) and ensure `init_db()` is idempotent
- [x] Call `init_db()` on application boot

### ⚡ CACHE-1 — Redis Integration

**Branch:** `feature/redis-cache`

- [x] Implement `src/cache/connection.py` with shared client singleton
- [x] Build `src/cache/cache.py` with helpers: `get_cached_recipe`, `set_cached_recipe` (with TTL), `delete_cached_recipe`, context management (`add_to_context`, `get_recent_context`), fail counters, and reset functions
- [x] Ensure all cache operations fail silently and never crash the application

### 🤖 AI-1 — Ollama Integration

**Branch:** `feature/ollama-integration`

- [x] Implement `src/ai/generator.py` with `_build_prompt`, `_parse_response` (strict regex for single lowercase word, reject compounds), and `generate_recipe`
- [x] Add configurable `OLLAMA_TIMEOUT` (default 100s) and HTTP retry logic (x2 attempts)
- [x] Add structured logging for all failure paths

### 🛡️ VAL-1 — Validation Layer

**Branch:** `feature/validation`

- [x] Create `src/validation.py` with `validate_inputs`, `validate_element`, and custom `ValidationError` exception
- [x] Handle normalisation, length checks, charset validation, and same-element rejection

### 🔄 CORE-1 — Combine Logic Pipeline

**Branch:** `feature/combine-core`

- [x] Implement `src/combine.py` with full `combine(a, b)` pipeline:
  - Input validation + normalisation (always sorted)
  - Check Redis → Postgres → Ollama (with AI validation retry loop, max 3 attempts)
  - Result validation, persistence to DB + cache + context
  - Return `CombineResult` (result, is_new, source, elapsed_ms)

---

## Definition of Done

- [x] All feature branches merged to `develop` via PR
- [x] `docker compose up` works cleanly with all services healthy
- [x] Core functionality smoke tested successfully (combine two base elements → new discovery persists and is cached)
- [x] This sprint document (`SPRINT_1.md`) is checked off and moved to `docs/`
- [x] No critical bugs remaining in scoped features
- [x] Structured logging and retries are in place for reliability
