.PHONY: setup ingest crm lint test

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

ingest:
	.venv/bin/python -m pipelines.download_data

crm:
	.venv/bin/python -m pipelines.generate_crm

lint:
	.venv/bin/ruff check .

test:
	.venv/bin/pytest
