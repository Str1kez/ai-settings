VENV := .venv/bin

.PHONY: check lint typecheck test rules-check fix install-dry install

check: lint typecheck test rules-check

lint:
	$(VENV)/ruff check .
	$(VENV)/ruff format --check .

typecheck:
	$(VENV)/mypy
	$(VENV)/mypy --python-version 3.10 scripts

test:
	$(VENV)/python -m pytest -q

rules-check:
	python3 scripts/sync.py rules --check

fix:
	$(VENV)/ruff check --fix .
	$(VENV)/ruff format .

install-dry:
	scripts/install.sh --dry-run

install:
	scripts/install.sh
