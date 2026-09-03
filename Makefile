.PHONY: lint format

package ?= ...

lint:
	uv run ruff check $(package)
	uv run ruff format --check $(package)
	uv run ty $(package)

format:
	uv run ruff check --fix $(package)
	uv run ruff format $(package)
