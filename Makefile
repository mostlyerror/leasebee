# 🐝 LeaseBee - Development Commands
# Usage: make <command>

.PHONY: help install dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend db-migrate db-upgrade clean

# Default target
help:
	@echo "🐝 LeaseBee Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies for both frontend and backend"
	@echo "  make install-backend  Install backend dependencies only"
	@echo "  make install-frontend Install frontend dependencies only"
	@echo ""
	@echo "Development (run both with one command):"
	@echo "  make dev              Start both backend and frontend (new tabs)"
	@echo "  make dev-backend      Start backend server only"
	@echo "  make dev-frontend     Start frontend dev server only"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Run backend tests"
	@echo "  make test-frontend    Run frontend tests"
	@echo "  make test-accuracy    Run accuracy tests"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       Create new migration (prompts for message)"
	@echo "  make db-upgrade       Run pending migrations"
	@echo "  make db-downgrade     Rollback last migration"
	@echo ""
	@echo "Linting:"
	@echo "  make lint             Lint both frontend and backend"
	@echo "  make lint-backend     Lint backend code"
	@echo "  make lint-frontend    Lint frontend code"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Clean build artifacts and caches"
	@echo "  make format           Format code (black + prettier)"
	@echo "  make type-check       Run type checking (mypy + tsc)"

# ============================================================================
# Installation
# ============================================================================

install: install-backend install-frontend
	@echo "✅ All dependencies installed!"

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install

# ============================================================================
# Development
# ============================================================================

# Start both backend and frontend in the same terminal with prefixed output
# Requires: npm install -g concurrently (or it will suggest it)
dev:
	@echo "🚀 Starting LeaseBee development servers..."
	@echo "   Backend:  http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo ""
	@which concurrently >/dev/null 2>&1 || (echo "📦 Installing concurrently..." && npm install -g concurrently)
	@concurrently \
		--names "BE,FE" \
		--prefix-colors "blue,green" \
		--kill-others-on-fail \
		"cd backend && source venv/bin/activate && uvicorn app.main:app --reload" \
		"cd frontend && npm run dev"

# Start both in separate Terminal tabs (macOS only)
dev-tabs:
	@echo "🚀 Starting LeaseBee in new Terminal tabs..."
	@osascript -e 'tell application "Terminal" to do script "cd $(PWD)/backend && source venv/bin/activate && uvicorn app.main:app --reload"' \
		-e 'tell application "Terminal" to do script "cd $(PWD)/frontend && npm run dev"' 2>/dev/null || \
	echo "❌ Could not open Terminal tabs. Try 'make dev' instead."

# Start only backend
dev-backend:
	@echo "🚀 Starting backend server..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Start only frontend
dev-frontend:
	@echo "🚀 Starting frontend dev server..."
	cd frontend && npm run dev

# ============================================================================
# Testing
# ============================================================================

test: test-backend test-frontend
	@echo "✅ All tests complete!"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && source venv/bin/activate && pytest tests/unit tests/accuracy -v

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test

test-accuracy:
	@echo "🎯 Running accuracy tests..."
	cd backend && source venv/bin/activate && pytest tests/accuracy/test_extraction_accuracy.py -v -s

# ============================================================================
# Database
# ============================================================================

db-migrate:
	@read -p "Migration message: " msg; \
	cd backend && source venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-upgrade:
	@echo "⬆️  Running database migrations..."
	cd backend && source venv/bin/activate && alembic upgrade head

db-downgrade:
	@echo "⬇️  Rolling back last migration..."
	cd backend && source venv/bin/activate && alembic downgrade -1

db-reset:
	@echo "⚠️  Dropping and recreating database..."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && \
	cd backend && source venv/bin/activate && alembic downgrade base && alembic upgrade head || \
	echo "Cancelled"

# ============================================================================
# Linting & Formatting
# ============================================================================

lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Linting backend..."
	cd backend && source venv/bin/activate && flake8 app tests --max-line-length=100 --ignore=E501,W503 || true
	@echo "✅ Backend lint check complete"

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint || true

format:
	@echo "✨ Formatting code..."
	cd backend && source venv/bin/activate && black app tests --line-length=100 2>/dev/null || echo "black not installed, skipping"
	cd frontend && npm run format 2>/dev/null || echo "format script not found, skipping"

type-check:
	@echo "🔍 Running type checks..."
	cd backend && source venv/bin/activate && mypy app 2>/dev/null || echo "mypy not installed, skipping"
	cd frontend && npm run type-check 2>/dev/null || npx tsc --noEmit 2>/dev/null || echo "TypeScript check skipped"

# ============================================================================
# Utilities
# ============================================================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

shell-backend:
	@echo "🐚 Opening backend shell..."
	cd backend && source venv/bin/activate && python

shell-db:
	@echo "🐚 Opening database shell..."
	cd backend && source venv/bin/activate && python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('Database session ready. Use db to query.')" -i

# ============================================================================
# Quick Navigation Shortcuts
# ============================================================================

# These are meant to be used with: make -C /path/to/leasebee <target>
# Or just: make <target> from the project root

.PHONY: be fe

be:
	@echo "cd $(PWD)/backend"

fe:
	@echo "cd $(PWD)/frontend"
