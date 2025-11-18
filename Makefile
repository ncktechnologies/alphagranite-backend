.PHONY: help build start stop restart logs shell migrate backup clean status health deploy

# Variables
DOCKER_COMPOSE = docker-compose
CONTAINER_NAME = alpha_granite_api

# Default target
help:
	@echo "Alpha Granite Backend - Management Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo "  build      - Build Docker images"
	@echo "  start      - Start all services"
	@echo "  stop       - Stop all services"
	@echo "  restart    - Restart all services"
	@echo "  logs       - Show application logs (follow mode)"
	@echo "  shell      - Open shell in web container"
	@echo "  migrate    - Run database migrations"
	@echo "  backup     - Create database backup"
	@echo "  clean      - Clean up containers and images"
	@echo "  status     - Show container status"
	@echo "  health     - Run health check"
	@echo "  deploy     - Full deployment (build and start)"
	@echo ""

# Build Docker images
build:
	@echo "Building Docker images..."
	@$(DOCKER_COMPOSE) build

# Start services
start:
	@echo "Starting services..."
	@$(DOCKER_COMPOSE) up -d
	@echo "✓ Services started"
	@make status

# Stop services
stop:
	@echo "Stopping services..."
	@$(DOCKER_COMPOSE) down
	@echo "✓ Services stopped"

# Restart services
restart:
	@echo "Restarting services..."
	@$(DOCKER_COMPOSE) restart
	@echo "✓ Services restarted"

# Show logs
logs:
	@echo "Showing logs (press Ctrl+C to exit)..."
	@$(DOCKER_COMPOSE) logs -f web

# Open shell in container
shell:
	@echo "Opening shell in web container..."
	@$(DOCKER_COMPOSE) exec web /bin/bash

# Run migrations
migrate:
	@echo "Running database migrations..."
	@$(DOCKER_COMPOSE) exec web python scripts/auto_migrate.py

# Create database backup
backup:
	@echo "Creating database backup..."
	@BACKUP_FILE="backup_$$(date +%Y%m%d_%H%M%S).sql" && \
	$(DOCKER_COMPOSE) exec -T web python -c "import os; from src.app.utils.config import DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME; print(f'pg_dump -h {DATABASE_HOST} -p {DATABASE_PORT} -U {DATABASE_USER} -d {DATABASE_NAME}')" | bash > $$BACKUP_FILE && \
	echo "✓ Backup created: $$BACKUP_FILE"

# Clean up
clean:
	@echo "Cleaning up containers and images..."
	@$(DOCKER_COMPOSE) down
	@docker system prune -f
	@echo "✓ Cleanup complete"

# Show status
status:
	@echo "Container status:"
	@$(DOCKER_COMPOSE) ps

# Health check
health:
	@echo "Running health check..."
	@if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✓ API is healthy"; \
		curl -s http://localhost:8000/health | python3 -m json.tool; \
	else \
		echo "✗ API is not responding"; \
		exit 1; \
	fi

# Full deployment
deploy:
	@echo "=========================================="
	@echo "Alpha Granite Backend - Deployment"
	@echo "=========================================="
	@if [ ! -f .env ]; then \
		echo "⚠ .env file not found!"; \
		echo "Copying .env.example to .env..."; \
		cp .env.example .env; \
		echo "✗ Please update .env file with your values before continuing!"; \
		exit 1; \
	fi
	@echo "✓ .env file found"
	@echo "Building and starting services..."
	@$(DOCKER_COMPOSE) down 2>/dev/null || true
	@$(DOCKER_COMPOSE) up -d --build
	@echo ""
	@echo "Waiting for services to be ready..."
	@sleep 5
	@make status
	@echo ""
	@echo "=========================================="
	@echo "✓ Deployment Complete!"
	@echo "=========================================="
	@echo ""
	@echo "Application is running at: http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"
	@echo "Health Check: http://localhost:8000/health"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs    - View application logs"
	@echo "  make status  - Check container status"
	@echo "  make health  - Run health check"
	@echo "  make stop    - Stop services"
	@echo ""
