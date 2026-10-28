.PHONY: setup ingest lint test

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

ingest:
	.venv/bin/python -m pipelines.download_data

lint:
	.venv/bin/ruff check .

test:
	.venv/bin/pytest
