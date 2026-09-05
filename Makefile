.PHONY: help install lint typecheck test unit integration seo aeo geo security regression api e2e meta mutation sentinel coverage gate serve demo clean

REPORTS ?= reports
PYTEST  ?= python -m pytest

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## install runtime and development dependencies
	python -m pip install -r requirements-dev.txt

lint: ## ruff
	python -m ruff check kontur tests tools

typecheck: ## mypy over the package
	python -m mypy kontur

test: ## the whole suite
	$(PYTEST) -q

unit integration api e2e security regression meta: ## one test level
	$(PYTEST) tests/$@ -q

seo aeo geo: ## one engine's tests
	$(PYTEST) -m $@ -q

mutation: ## mutation campaign over the critical modules
	python -m tools.mutation.runner --json $(REPORTS)/mutation.json

sentinel: ## T-META-001 — can the suite detect a controlled break?
	python -m tools.mutation.sentinel --json $(REPORTS)/sentinel.json

coverage: ## coverage report
	$(PYTEST) -q --cov=kontur --cov-report=term-missing --cov-report=json:$(REPORTS)/coverage.json

gate: ## the final quality gate
	python -m tools.quality_gate --reports $(REPORTS)

serve: ## run the dashboard on :8000
	python -m kontur.api.serve

demo: ## print the GET-parameter table for the demo workspace
	python -m kontur.cli params

clean:
	rm -rf $(REPORTS) .coverage .pytest_cache **/__pycache__
