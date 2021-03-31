PYTHON ?= python3
POETRY ?= $(PYTHON) -m poetry

help:
	@cat .makefile-help

install:
	$(POETRY) update
	$(POETRY) install

fmt:
	$(POETRY) run isort --atomic .
	$(POETRY) run black .

fmt-check:
	$(POETRY) run isort --check-only .
	$(POETRY) run black --check .

lint:
	$(POETRY) run pylint log_with_context.py test_log_with_context.py
	$(POETRY) run mypy log_with_context.py test_log_with_context.py

build:
	$(POETRY) run python -m pip --no-cache-dir wheel --no-deps .

test:
	$(POETRY) run python -m unittest

.PHONY: help fmt fmt-check lint build test
