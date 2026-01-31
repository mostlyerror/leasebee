.PHONY: start start-backend start-frontend stop install help migrate migration

start:
	@echo "Starting LeaseBee..."
	@make -j2 start-backend start-frontend

start-backend:
	@echo "Starting backend on http://localhost:8000"
	@cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-frontend:
	@echo "Starting frontend on http://localhost:3000"
	@cd frontend && npm run dev

stop:
	@echo "Stopping all processes..."
	@pkill -f "uvicorn app.main:app" || true
	@pkill -f "next dev" || true
	@echo "Stopped."

install:
	@echo "Installing backend dependencies..."
	@cd backend && python -m venv venv && ./venv/bin/pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Done!"

migrate:
	@echo "Running database migrations..."
	@cd backend && ./venv/bin/alembic upgrade head

migration:
	@read -p "Enter migration message: " msg; \
	cd backend && ./venv/bin/alembic revision --autogenerate -m "$$msg"

help:
	@echo "Available commands:"
	@echo "  make start          - Start both backend and frontend"
	@echo "  make start-backend  - Start only backend"
	@echo "  make start-frontend - Start only frontend"
	@echo "  make stop           - Stop all running processes"
	@echo "  make install        - Install all dependencies"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migration      - Create a new migration"
	@echo "  make help           - Show this help message"
