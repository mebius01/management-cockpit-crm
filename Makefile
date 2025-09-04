# Makefile for Django Entity Management CRM

.PHONY: help dev-venv dev-setup dev-run dev-migrate dev-fixtures dev-shell dev-test up up-dev up-db up-app down down-db down-app logs logs-db migrate fixtures clean

# Default target
help:
	@echo "Development commands (local):"
	@echo "  make dev-venv        - Activate virtual environment"
	@echo "  make dev-setup       - Setup development environment"
	@echo "  make dev-run         - Run development server"
	@echo "  make dev-migrate     - Run migrations locally"
	@echo "  make dev-fixtures    - Load fixtures locally"
	@echo "  make dev-shell       - Open Django shell locally"
	@echo "  make dev-test        - Run tests locally"
	@echo ""
	@echo "Docker commands:"
	@echo "  make up              - Start both database and application"
	@echo "  make up-dev          - Start development with hot reload"
	@echo "  make up-db           - Start only database"
	@echo "  make up-app          - Start only application"
	@echo "  make down            - Stop all services"
	@echo "  make down-db         - Stop only database"
	@echo "  make down-app        - Stop only application"
	@echo "  make logs            - Show application logs"
	@echo "  make logs-db         - Show database logs"
	@echo "  make migrate         - Run database migrations (Docker)"
	@echo "  make fixtures        - Load fixtures (Docker)"
	@echo "  make clean           - Clean up containers and volumes"

# Development commands (local)
dev-venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment with Python 3.13..."; \
		python3.13 -m venv .venv; \
	fi
	@echo "Virtual environment ready!"
	@echo "Activate with: source .venv/bin/activate"

dev-setup:
	pip install -e .
	pip install -e ".[dev]"

dev-run:
	python manage.py runserver

dev-migrate:
	python manage.py migrate

dev-fixtures:
	python manage.py loaddata entity/fixtures/*.json

dev-shell:
	python manage.py shell

dev-test:
	python -m pytest

# Docker commands
up:
	docker compose up -d

up-dev:
	docker compose -f docker-compose.dev.yml up -d

up-db:
	docker compose -f docker-compose.pg.yml up -d

up-app:
	docker compose -f docker-compose.app.yml up -d

down:
	docker compose down

down-db:
	docker compose -f docker-compose.pg.yml down

down-app:
	docker compose -f docker-compose.app.yml down

logs:
	docker compose logs -f crm-app

logs-db:
	docker compose logs -f crm-pg

migrate:
	docker compose exec crm-app python manage.py migrate

fixtures:
	docker compose exec crm-app python manage.py loaddata entity/fixtures/*.json

clean:
	docker compose down -v
	docker system prune -f
