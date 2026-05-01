.PHONY: help up down restart logs ps \
        pull-model setup dev shell \
        db-shell redis-shell \
        test test-all lint clean nuke \
		serve serve-prod \
		clear-db clear-redis clear-all

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_MODEL ?= llama3
PYTHON       := uv run python

# ── Help ──────────────────────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  OLLAMA_MODEL=$(OLLAMA_MODEL)  (override with: make pull-model OLLAMA_MODEL=mistral)"

# ── Docker ────────────────────────────────────────────────────────────────────
up: ## Start all services (postgres, redis, ollama)
	docker compose up -d --build
	@echo "✅ All services up"

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs from all services
	docker compose logs -f

ps: ## Show service status
	docker compose ps

# ── Ollama model ──────────────────────────────────────────────────────────────
pull-model: ## Pull the Ollama model (default: llama3)
	@echo "📦 Pulling $(OLLAMA_MODEL)..."
	docker compose exec ollama ollama pull $(OLLAMA_MODEL)

# ── Project setup ─────────────────────────────────────────────────────────────
setup: up ## Full first-time setup: start services + copy .env + install deps
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env from .env.example — edit if needed"; \
	fi
	uv sync
	@echo "✅ Setup complete. Run 'make pull-model' to download the LLM."

install: ## Install / sync Python dependencies only
	uv sync

# ── Running the game ──────────────────────────────────────────────────────────
dev: ## Run the CLI game
	$(PYTHON) main.py

shell: ## Open a Python REPL inside the venv
	uv run python

# ── Database & cache shells ───────────────────────────────────────────────────
db-shell: ## Open a psql shell
	docker compose exec postgres psql -U alchemy -d alchemy

redis-shell: ## Open a redis-cli shell
	docker compose exec redis redis-cli

# ── Makefile additions for Phase 10 ──────────────────────────────────────────
# Add these targets to your existing Makefile

serve:
	uv run uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

serve-prod:
	uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4

# ── Testing ───────────────────────────────────────────────────────────────────
test: ## Run offline unit tests (no services needed)
	uv sync --group dev
	uv run pytest -m unit -v

test-all: ## Run all tests including integration (requires make up)
	uv sync --group dev
	uv run pytest -v

# ── Quality ───────────────────────────────────────────────────────────────────
lint: ## Lint with ruff
	uv run ruff check src/ tests/ main.py --fix

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 Cleaned"

nuke: ## ⚠️  Stop services AND delete all volumes (wipes DB + Redis data)
	docker compose down -v
	@echo "💥 All volumes deleted"

# ── Makefile additions: clear DB and Redis ───────────────────────────────────
# Add these targets to your existing Makefile

clear-db:
	docker compose exec postgres psql -U alchemy -d alchemy -c \
		"TRUNCATE TABLE recipes; DELETE FROM elements WHERE name NOT IN ('fire','water','earth','air');"

clear-redis:
	docker compose exec redis redis-cli FLUSHDB

clear-all: clear-redis clear-db
	@echo "Redis + DB cleared. Base elements kept."
