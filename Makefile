# The single source of truth for every check. CI runs these exact targets - if `make ci`
# passes locally it passes on GitHub, and there is no second list to keep in sync.
.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck lines spec sec workflows test-unit test-integration test ci run migrate shell graph

# pipefail: a pipeline fails when any stage fails, not only the last one.
SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

# Pinned tool versions, run through uvx so none of them is a project dependency (ADR 0003).
PIP_AUDIT_VERSION  := 2.10.1
ZIZMOR_VERSION     := 1.31.1
ACTIONLINT_VERSION := 1.7.12.25

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Create the venv and install every dependency from the lockfile
	uv sync

lint: ## Lockfile check + ruff lint + format check
	uv lock --check
	uv run ruff check src scripts
	uv run ruff format --check src scripts

format: ## Rewrite code to satisfy the formatter and autofixable lints
	uv run ruff check --fix src scripts
	uv run ruff format src scripts

typecheck: ## mypy --strict over the application
	uv run mypy src

lines: ## Fail on any file longer than the agent-readable limit
	uv run python scripts/check_file_length.py

spec: ## Fail when application code changes without a merged, approved spec
	uv run python scripts/check_spec.py

sec: ## Known vulnerabilities in locked dependencies + secrets anywhere in git history
	uv export --frozen --format requirements-txt --no-emit-project --quiet \
		| uvx pip-audit@$(PIP_AUDIT_VERSION) --strict --disable-pip -r /dev/stdin
	@if command -v gitleaks >/dev/null; then gitleaks git --redact --no-banner .; \
	else echo "gitleaks not installed (brew install gitleaks) - CI runs it"; fi

workflows: ## Lint GitHub Actions workflows: syntax (actionlint) and security (zizmor)
	uvx --from actionlint-py==$(ACTIONLINT_VERSION) actionlint
	uvx zizmor@$(ZIZMOR_VERSION) .github/workflows

test-unit: ## Fast tests: no database, no containers
	uv run pytest -m unit

test-integration: ## Real Postgres via testcontainers - needs a running Docker daemon
	uv run pytest -m integration

test: test-unit test-integration ## Every test

ci: lint lines typecheck test spec sec workflows ## Everything CI enforces, in CI's order

run: ## Serve the API on http://localhost:8000/api/docs
	uv run uvicorn config.asgi:application --reload --app-dir src

migrate: ## Apply migrations to the local dev database
	uv run python manage.py migrate

shell: ## Django shell against the dev database
	uv run python manage.py shell

graph: ## Rebuild the local codegraph index
	codegraph index .
