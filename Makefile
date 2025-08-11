.PHONY: help install install-dev test test-cov lint format clean build publish demo

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	pip install -e .

install-dev:  ## Install the package with development dependencies
	pip install -e .[dev]

test:  ## Run tests
	python -m pytest tests/ -v

test-cov:  ## Run tests with coverage
	python -m pytest tests/ --cov=observables --cov-report=term-missing --cov-report=html

lint:  ## Run linting checks
	black --check observables tests
	isort --check-only observables tests
	flake8 observables tests
	mypy observables

format:  ## Format code with black and isort
	black observables tests
	isort observables tests

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build the package
	python -m build

publish:  ## Build and publish to PyPI (requires twine)
	python -m build
	twine upload dist/*

demo:  ## Run the demo script
	python observables/examples/demo.py

check:  ## Run all checks (lint + test)
	$(MAKE) lint
	$(MAKE) test

pre-commit:  ## Run pre-commit checks
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

docs:  ## Build documentation
	cd docs && make html

docs-serve:  ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8000
