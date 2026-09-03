.PHONY: lint format test check

package ?= src tests

lint:
	uv run ruff check $(package)
	uv run ruff format --check $(package)
	uv run ty check $(package)

format:
	uv run ruff check --fix $(package)
	uv run ruff format $(package)

test:
	uv run pytest

check: lint test
