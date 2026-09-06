# Developer entry points. `make` with no target prints this list.
COMPOSE ?= docker compose
LOCAL_DATABASE_URL ?= postgresql+asyncpg://alma:alma@localhost:5432/alma

.DEFAULT_GOAL := help
.PHONY: help up down logs ps build test test-backend test-frontend lint lint-backend lint-frontend migrate seed clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.env:
	cp .env.example .env

up: .env ## Build and start db, mailpit, api, web (detached)
	$(COMPOSE) up -d --build
	@echo ""
	@echo "  Public lead form : http://localhost:3000"
	@echo "  Internal UI      : http://localhost:3000/leads"
	@echo "  API docs         : http://localhost:8000/docs"
	@echo "  Mailpit inbox    : http://localhost:8025"
	@echo ""

down: ## Stop all services (keeps volumes)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f --tail=100

ps: ## Show service status
	$(COMPOSE) ps

build: ## Rebuild images without starting
	$(COMPOSE) build

test: test-backend ## Run the test suite (backend; needs Docker for Postgres)

test-backend: ## Run pytest against the compose Postgres
	$(COMPOSE) up -d --wait db
	cd backend && DATABASE_URL=$(LOCAL_DATABASE_URL) EMAIL_PROVIDER=console STORAGE_PROVIDER=local STORAGE_LOCAL_DIR=$${TMPDIR:-/tmp}/alma-resumes uv run pytest

test-frontend: ## Type-check the frontend
	cd frontend && npx tsc --noEmit

lint: lint-backend lint-frontend ## Run all linters and type checkers

lint-backend: ## ruff + mypy
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .

lint-frontend: ## eslint + tsc
	cd frontend && npm run lint && npx tsc --noEmit

migrate: ## Apply Alembic migrations inside the api container
	$(COMPOSE) exec api alembic upgrade head

seed: ## Create/refresh the attorney login inside the api container
	$(COMPOSE) exec api python -m app.seed

clean: ## Stop services and delete volumes (database and stored resumes)
	$(COMPOSE) down -v --remove-orphans
