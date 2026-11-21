.PHONY: help up down restart logs ps \
        pull-model setup install hooks dev shell \
        db-shell redis-shell \
        serve serve-prod \
        test test-all lint format typecheck check \
        clean nuke clear-db clear-redis clear-all

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
setup: up hooks ## Full first-time setup: services + .env + deps + git hooks
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env from .env.example — edit if needed"; \
	fi
	uv sync
	@echo "✅ Setup complete. Run 'make pull-model' to download the LLM."

install: ## Install / sync Python dependencies only
	uv sync

hooks: ## Install git hooks once: commit, commit-msg, pre-push
	uv run pre-commit install --install-hooks

# ── Running the game ──────────────────────────────────────────────────────────
dev: ## Run the CLI game
	$(PYTHON) main.py

shell: ## Open a Python REPL inside the venv
	uv run python

serve: ## API dev server (hot reload)
	uv run uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## API production server (4 workers)
	uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4

# ── Database & cache shells ───────────────────────────────────────────────────
db-shell: ## Open a psql shell
	docker compose exec postgres psql -U alchemy -d alchemy

redis-shell: ## Open a redis-cli shell
	docker compose exec redis redis-cli

# ── Testing ───────────────────────────────────────────────────────────────────
test: ## Run offline unit tests with coverage (no services needed)
	uv run pytest -m unit --cov --cov-report=term-missing

test-all: ## Run all tests including integration (requires make up)
	uv run pytest --cov --cov-report=term-missing

# ── Quality ───────────────────────────────────────────────────────────────────
lint: ## Run all pre-commit hooks except mypy and branch guard (fixes files)
	SKIP=no-commit-to-branch,mypy uv run pre-commit run --all-files

format: ## Fix ruff lint and formatting issues
	uv run ruff check --fix src tests main.py
	uv run ruff format src tests main.py

typecheck: ## Run strict mypy
	uv run mypy src tests main.py

check: lint typecheck test ## Full local quality gate

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 Cleaned"

nuke: ## ⚠️  Stop services AND delete all volumes (wipes DB + Redis data)
	docker compose down -v
	@echo "💥 All volumes deleted"

clear-db: ## ⚠️  Truncate recipes, keep base elements
	docker compose exec postgres psql -U alchemy -d alchemy -c \
		"TRUNCATE TABLE recipes; DELETE FROM elements WHERE name NOT IN ('fire','water','earth','air');"

clear-redis: ## ⚠️  Flush Redis
	docker compose exec redis redis-cli FLUSHDB

clear-all: clear-redis clear-db ## ⚠️  Reset Redis + DB, keep base elements
	@echo "Redis + DB cleared. Base elements kept."
