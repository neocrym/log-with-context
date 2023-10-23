PYTHON ?= python3
POETRY ?= $(PYTHON) -m poetry

help:
	@cat .makefile-help
.PHONY: help

update:
	$(POETRY) update
.PHONY: update

install:
	$(POETRY) install
.PHONY: install

fmt:
	$(POETRY) run isort --atomic .
	$(POETRY) run black .
.PHONY: fmt

fmt-check:
	$(POETRY) run isort --check-only .
	$(POETRY) run black --check .
.PHONY: fmt-check

mypy:
	$(POETRY) run mypy --strict log_with_context/__init__.py test_log_with_context.py
.PHONY: mypy

pylint:
	$(POETRY) run pylint log_with_context/__init__.py test_log_with_context.py
.PHONY: pylint

lint: pylint mypy
.PHONY: lint

build:
	$(POETRY) run python -m pip --no-cache-dir wheel --no-deps .
.PHONY: build

test:
	$(POETRY) run python -m unittest
.PHONY: test
