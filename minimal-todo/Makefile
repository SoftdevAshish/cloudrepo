.PHONY: install run test lint
install:
	pip install -r requirements-dev.txt
run:
	uvicorn app.main:app --reload
test:
	pytest -q
lint:
	ruff check . && ruff format --check .
