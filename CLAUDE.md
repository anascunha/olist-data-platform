# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Local Development (venv)

```bash
make setup          # Create .venv and install requirements
make ingest         # Kaggle -> governance filter -> UC Volume (python -m pipelines.download_data)
make lint           # ruff check .
make test           # pytest
```

### Running Streamlit UI

```bash
docker-compose exec data_platform streamlit run <app_file>.py
# Accessible at http://localhost:8501
```

### Testing

```bash
pytest                              # Run all tests
pytest tests/pipelines/             # Run only pipeline tests
pytest tests/pipelines/test_download_data.py::TestDownloadOlistDatasetSuccess  # Single class
pytest -k "test_creates_download"   # Match by name pattern
```

Tests live in `tests/` and mirror the source tree (e.g. `pipelines/download_data.py` → `tests/pipelines/test_download_data.py`). External calls (Kaggle CLI, Databricks CLI via subprocess) are mocked; Bronze tests use a local SparkSession (skipped if Java/pyspark are missing).

### Linting

```bash
ruff check .        # Python linting (also runs in CI)
```

### CI Pipeline

The `.github/workflows/ci.yml` runs:
1. Python linting with Ruff (`ruff check .`)
2. Python unit tests (`pytest --tb=short -v`, with Java for the local-Spark tests)

## Architecture

The platform implements a **Medallion Architecture** for the [Olist Brazilian E-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) with a zero-budget approach using free tiers.

### Data Layers

| Layer  | Purpose | Tool |
|--------|---------|------|
| Bronze | CSVs in UC Volume -> Delta tables `raw.source_olist.*` | PySpark notebook `databricks/ingestao_bronze.py` |
| Silver | Cleaned, deduplicated data | PySpark on Databricks |
| Gold   | Dimensional model (Star Schema) | dbt-databricks |

### Infrastructure (Databricks Unity Catalog)

Provisioned by `databricks/setup/setup_catalogs_schemas.sql` (mirrors the Adventure Works project):

```
raw.source_olist (+ Volume landing)   ← Bronze Olist
raw.source_crm   (+ Volume landing)   ← Bronze CRM
sandbox.dbt_<user>                     ← dbt dev target
producao.staging / trusted / marts     ← Silver / Gold (dbt prod target)
```

Names are centralised in `pipelines/config.py` (overridable via `UC_*` env vars). Bronze logic lives in `pipelines/bronze.py` so it can be unit-tested with local Spark; notebooks are thin wrappers.

### AI / NL2SQL Agent (planned)

LangChain + Llama 3 (via Groq API) translates natural language questions into Databricks SQL queries, exposed through a Streamlit UI. Agent code goes in `ml_ops/`.

### Key Directories

- `pipelines/` — Data ingestion scripts (Kaggle download, CRM generator, Bronze logic, UC config)
- `databricks/` — Databricks notebooks (source format) and UC setup SQL
- `transform/` — dbt models (not yet populated)
- `ml_ops/` — LangChain NL2SQL agent (not yet populated)

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
KAGGLE_USERNAME / KAGGLE_KEY      # Kaggle dataset download
DATABRICKS_HOST / DATABRICKS_TOKEN / DATABRICKS_HTTP_PATH                # Databricks
GROQ_API_KEY                      # Llama 3 via Groq
```

## Tech Stack

- **Python 3.11**, PySpark, Delta Lake
- **dbt Core** + `dbt-databricks` adapter
- **LangChain** + `langchain-groq` (Llama 3)
- **Streamlit** (analytics UI, port 8501)
- **Ruff** (linting), **pytest** + **pytest-mock** (tests)
- **Docker** / **Docker Compose** for local dev

## Development Phases

The project is being built incrementally:
1. Infrastructure setup and documentation *(done)*
2. Data ingestion pipeline (Kaggle -> UC Volume -> Bronze Delta)
   - Phase 3: fictional CRM generator (`pipelines/generate_crm.py`, `make crm`) linked to Olist by `customer_unique_id`, landed in `raw.source_crm`
3. Unit tests (pytest) *(done — `tests/pipelines/`)*
4. dbt tests and SQL linting (sqlfluff)
5. Streamlit analytics UI
