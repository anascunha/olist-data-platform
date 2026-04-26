.PHONY: setup ingest lint test

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

ingest:
	.venv/bin/python pipelines/download_data.py

lint:
	.venv/bin/ruff check .

test:
	.venv/bin/pytest
