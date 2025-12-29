.PHONY: help init dev up down restart rebuild logs clean test lint format verify reset-db health

help:
	@echo "Available commands:"
	@echo "  make init      - Initialize development environment"
	@echo "  make dev       - Start development environment"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart backend service"
	@echo "  make rebuild   - Rebuild backend image and restart"
	@echo "  make logs      - Show logs"
	@echo "  make clean     - Clean up containers and volumes"
	@echo "  make reset-db  - Clear database tables (candidates, pages, etc.)"
	@echo "  make health    - Check service health"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linter"
	@echo "  make format    - Format code"
	@echo "  make verify    - Verify upload endpoint"

init:
	@echo "Initializing development environment..."
	@cp -n .env.example .env || true
	@echo "Environment file created. Please review .env"

dev: init
	docker-compose up -d
	@echo "Development environment started!"
	@echo "MinIO Console: http://localhost:9001"
	@echo "API Docs: http://localhost:8080/docs"

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	@echo "Restarting backend service..."
	docker-compose restart doc_process
	@echo "Waiting for service to be healthy..."
	@sleep 3
	@make health

rebuild:
	@echo "Rebuilding backend image..."
	docker-compose build doc_process
	@echo "Restarting service..."
	docker-compose restart doc_process
	@echo "Waiting for service to be healthy..."
	@sleep 5
	@make health

logs:
	docker-compose logs -f doc_process

clean:
	docker-compose down -v
	rm -rf services/doc_process/src/__pycache__
	rm -rf services/doc_process/tests/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

reset-db:
	@echo "Clearing database tables..."
	@docker-compose exec -T postgres psql -U postgres -d ppt_editor -c "TRUNCATE TABLE candidates CASCADE;" 2>/dev/null || true
	@docker-compose exec -T postgres psql -U postgres -d ppt_editor -c "TRUNCATE TABLE pages CASCADE;" 2>/dev/null || true
	@docker-compose exec -T postgres psql -U postgres -d ppt_editor -c "TRUNCATE TABLE patches CASCADE;" 2>/dev/null || true
	@docker-compose exec -T postgres psql -U postgres -d ppt_editor -c "TRUNCATE TABLE projects CASCADE;" 2>/dev/null || true
	@echo "Database tables cleared!"

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8080/health | python3 -m json.tool || echo "Service not responding"

test:
	docker-compose exec doc_process pytest tests/ -v

lint:
	docker-compose exec doc_process ruff check src/ tests/

format:
	docker-compose exec doc_process black src/ tests/
	docker-compose exec doc_process ruff check --fix src/ tests/

# 快速验证上传功能
verify:
	@echo "Verifying upload endpoint..."
	@curl -X POST http://localhost:8080/v1/assets/upload \
		-F "file=@testdata/images/sample_slide.png" \
		| python3 -m json.tool
