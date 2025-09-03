# Management Cockpit CRM - Test Commands

.PHONY: help test test-unit test-api test-integration test-all test-coverage test-fast test-postgres clean-test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit/ -m unit

test-api: ## Run API tests only
	pytest tests/api/ -m api

test-integration: ## Run integration tests only
	pytest tests/integration/ -m integration

test-performance: ## Run performance tests only
	pytest tests/performance/ -m performance

test-all: ## Run all tests with coverage
	pytest --cov=app --cov=entity --cov=services --cov-report=html --cov-report=term-missing

test-coverage: ## Run tests with coverage report
	pytest --cov=app --cov=entity --cov=services --cov-report=html:htmlcov --cov-report=term-missing --cov-fail-under=80

test-fast: ## Run fast tests (exclude slow and postgres tests)
	pytest -m "not slow and not postgres"

test-postgres: ## Run tests with PostgreSQL (requires USE_POSTGRES_TESTS=1)
	USE_POSTGRES_TESTS=1 pytest -m postgres

test-scd2: ## Run SCD2 specific tests
	pytest -m scd2

test-audit: ## Run audit related tests
	pytest -m audit

test-temporal: ## Run temporal query tests
	pytest -m temporal

test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw

lint: ## Run linting
	ruff check .
	black --check .

lint-fix: ## Fix linting issues
	ruff check --fix .
	black .

type-check: ## Run type checking
	mypy .

clean-test: ## Clean test artifacts
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf test_media/
	rm -rf test_static/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

install-test-deps: ## Install test dependencies
	pip install -e ".[dev]"

setup-test-db: ## Setup test database (PostgreSQL)
	docker-compose up -d crm-pg
	sleep 5
	USE_POSTGRES_TESTS=1 python manage.py migrate --settings=app.test_settings

# Development helpers
dev-setup: ## Setup development environment
	pip install -e ".[dev]"
	cp .env.example .env
	docker-compose up -d crm-pg
	sleep 5
	python manage.py migrate
	python manage.py loaddata entity/fixtures/*.json

dev-test: ## Run tests in development mode
	pytest -v --tb=short

# CI/CD helpers
ci-test: ## Run tests for CI/CD
	pytest --cov=app --cov=entity --cov=services --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

ci-test-postgres: ## Run PostgreSQL tests for CI/CD
	USE_POSTGRES_TESTS=1 pytest -m postgres --cov=app --cov=entity --cov=services --cov-report=xml --junitxml=test-results-postgres.xml
