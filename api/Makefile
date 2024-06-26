BIN_DIR ?= .venv/bin
ALL = api


venv:
	python3 -m venv .venv
	$(BIN_DIR)/pip install -U pip setuptools
	$(BIN_DIR)/pip install poetry
	$(BIN_DIR)/poetry install


lint:
	$(BIN_DIR)/mypy $(ALL)


format:
	$(BIN_DIR)/isort $(ALL)
	$(BIN_DIR)/black --line-length 120 --skip-string-normalization $(ALL)
	$(BIN_DIR)/autoflake --recursive --in-place --remove-all-unused-imports --ignore-init-module-imports $(ALL)
	$(BIN_DIR)/unify --in-place --recursive --quote '"' $(ALL)


dev:
	$(BIN_DIR)/fastapi dev api/main.py
