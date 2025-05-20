.PHONY: install install-dev clean test lint format check

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

test:
	pytest

lint:
	ruff check .
	mypy .

format:
	black .
	isort .
	ruff check --fix .

check: lint test

build:
	python -m build

publish:
	python -m twine upload dist/* 