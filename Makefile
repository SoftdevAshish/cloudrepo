.PHONY: install lint format typecheck test audit check run worker beat up
install:
	pip install -r requirements-dev.txt && pre-commit install
lint:
	ruff check . && ruff format --check .
format:
	ruff check --fix . && ruff format .
typecheck:
	mypy app
test:
	pytest
audit:
	pip-audit -r requirements.txt
check: lint typecheck test
run:
	uvicorn app.main:app --reload
worker:
	celery -A app.celery_app worker -l info
beat:
	celery -A app.celery_app beat -l info
up:
	docker compose up --build
