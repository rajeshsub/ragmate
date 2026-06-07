.PHONY: bootstrap dev test lint format coverage build clean docs

VENV := .venv

# Cross-platform: Windows uses Scripts/, Unix uses bin/
ifeq ($(OS),Windows_NT)
    BIN    := $(VENV)/Scripts
    PYTHON := py -3.13
else
    BIN    := $(VENV)/bin
    PYTHON := python3.13
endif

# sh-compatible for both Git Bash on Windows and Unix
COPY_ENV := test -f .env || cp .env.example .env

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install
	$(COPY_ENV)
	@echo "Bootstrap complete. Edit .env then run: make dev"

dev:
	$(BIN)/uvicorn ragmate.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(BIN)/pytest

coverage:
	$(BIN)/pytest --cov=ragmate --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

lint:
	$(BIN)/ruff check ragmate tests
	$(BIN)/mypy ragmate
	$(BIN)/bandit -r ragmate -c pyproject.toml

format:
	$(BIN)/ruff check --fix ragmate tests
	$(BIN)/black ragmate tests

build:
	docker build -t ragmate:latest .

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docs:
	$(BIN)/python -c "import json; import ragmate.main as m; print(json.dumps(m.app.openapi(), indent=2))" > openapi.json
	@echo "OpenAPI spec written to openapi.json"
