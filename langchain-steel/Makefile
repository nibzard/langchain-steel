.PHONY: install install-dev test test-unit test-integration test-cov lint format type-check clean docs docs-serve build publish help

# Default Python and pip commands
PYTHON := python3
PIP := pip3

# Development commands
help:			## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install:		## Install package dependencies
	$(PIP) install -e .

install-dev:		## Install package with development dependencies
	$(PIP) install -e ".[dev]"
	pre-commit install

test:			## Run all tests
	pytest

test-unit:		## Run unit tests only
	pytest -m "not integration"

test-integration:	## Run integration tests only  
	pytest -m integration

test-cov:		## Run tests with coverage report
	pytest --cov=langchain_steel --cov-report=html --cov-report=term-missing

lint:			## Run linting (flake8)
	flake8 langchain_steel tests examples

format:			## Format code with black and isort
	black langchain_steel tests examples
	isort langchain_steel tests examples

format-check:		## Check code formatting without making changes
	black --check langchain_steel tests examples
	isort --check-only langchain_steel tests examples

type-check:		## Run type checking with mypy
	mypy langchain_steel

quality:		## Run all quality checks (lint, format-check, type-check)
	$(MAKE) lint
	$(MAKE) format-check  
	$(MAKE) type-check

clean:			## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:			## Build documentation
	cd docs && make html

docs-serve:		## Serve documentation locally
	cd docs && make html && python -m http.server 8000 -d _build/html

build:			## Build package for distribution
	$(PYTHON) -m build

publish-test:		## Publish to PyPI test repository
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish:		## Publish to PyPI
	$(PYTHON) -m twine upload dist/*

# Development workflow commands
dev-setup:		## Complete development environment setup
	$(MAKE) install-dev
	$(MAKE) pre-commit-install

pre-commit-install:	## Install pre-commit hooks
	pre-commit install

pre-commit-run:		## Run pre-commit on all files
	pre-commit run --all-files

test-quick:		## Run quick test subset for development
	pytest tests/unit/ -x -v

# CI/CD simulation
ci-test:		## Simulate CI testing pipeline
	$(MAKE) quality
	$(MAKE) test-cov

# Docker commands (if needed)
docker-build:		## Build Docker image for testing
	docker build -t langchain-steel:dev .

docker-test:		## Run tests in Docker container
	docker run --rm langchain-steel:dev make test