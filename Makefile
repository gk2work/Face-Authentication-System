# Face Authentication System - Makefile
# Convenient commands for Docker and development

.PHONY: help build up down restart logs shell test clean

help: ## Show this help message
	@echo "Face Authentication System - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"

up-dev: ## Start services in development mode with hot reload
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-app: ## View logs from app service only
	docker-compose logs -f app

shell: ## Open shell in app container
	docker-compose exec app /bin/bash

shell-db: ## Open MongoDB shell
	docker-compose exec mongodb mongosh face_auth

test: ## Run tests in container
	docker-compose exec app pytest tests/ -v

clean: ## Stop and remove all containers, volumes, and images
	docker-compose down -v --rmi all

ps: ## Show running containers
	docker-compose ps

health: ## Check health of services
	@echo "Checking API health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"
	@echo ""
	@echo "Checking MongoDB..."
	@docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet || echo "MongoDB not responding"

init: ## Initialize the system (first time setup)
	@echo "Creating storage directories..."
	@mkdir -p backend/storage/photographs backend/storage/vector_db backend/logs
	@echo "Building Docker images..."
	@docker-compose build
	@echo "Starting services..."
	@docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "System initialized! API available at http://localhost:8000"

mongo-express: ## Start MongoDB Express for database management
	docker-compose --profile tools up -d mongo-express
	@echo "MongoDB Express available at http://localhost:8081"
	@echo "Username: admin, Password: admin"

backup-db: ## Backup MongoDB database
	@echo "Backing up database..."
	@docker-compose exec -T mongodb mongodump --db face_auth --out /data/backup
	@docker cp face-auth-mongodb:/data/backup ./backup_$(shell date +%Y%m%d_%H%M%S)
	@echo "Backup completed"

restore-db: ## Restore MongoDB database (usage: make restore-db BACKUP=backup_20231031_120000)
	@echo "Restoring database from $(BACKUP)..."
	@docker cp $(BACKUP) face-auth-mongodb:/data/restore
	@docker-compose exec mongodb mongorestore --db face_auth /data/restore/face_auth
	@echo "Restore completed"
