.PHONY: build check clean compile format lint pre-commit test

build:
	uv build

check: lint test build

clean:
	rm -rf build dist .pytest_cache .ruff_cache *.egg-info

compile:
	uv run basemode-evidence compile

format:
	uv run ruff check --fix src tests
	uv run ruff format src tests

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

pre-commit:
	uv run pre-commit run --all-files

test:
	uv run pytest --cov --cov-report=term-missing
