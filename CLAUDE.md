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

### Streamlit UI (planned — no app yet)

`Dockerfile` / `docker-compose.yml` exist for a future analytics UI; there is no Streamlit app in the repo yet.

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

### dbt

```bash
cd transform && set -a && source .env && set +a
dbt deps --profiles-dir .
dbt build --profiles-dir .                 # dev
TARGET_ENV=prod dbt build --profiles-dir . # prod
```

Conventions mirror the Adventure Works project: `stg_<source>__<table>`, `tru_<entity>`, `dim_/fct_/agg_`, one `.yml` per model, leading commas, generic tests with `arguments:`. Valid orders exclude `var('invalid_order_statuses')`; recency is measured against the dataset's last order (historical snapshot).

### CI Pipeline

The `.github/workflows/ci.yml` runs:
1. Python linting with Ruff (`ruff check .`)
2. Python unit tests (`pytest --tb=short -v`, with Java for the local-Spark tests)
3. dbt `deps` + `parse` for `dev` and `prod` targets

## Architecture

The platform implements a **Medallion Architecture** for the [Olist Brazilian E-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) with a zero-budget approach using free tiers.

### Data Layers

| Layer  | Purpose | Tool |
|--------|---------|------|
| Bronze | CSVs in UC Volume -> Delta tables `raw.source_olist.*` | PySpark notebook `databricks/ingestao_bronze.py` |
| Silver | `stg_*` (typing/renaming, 1:1) + `tru_*` (business rules, CRM dedup) | dbt-databricks (`transform/models/staging`, `trusted`) |
| Gold   | `dim_*`, `fct_orders`, `agg_crm_*` (CRM x marketplace purchases) | dbt-databricks (`transform/models/marts`) |

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
- `transform/` — dbt project (profile `olist`, targets `dev` → `sandbox.<schema>`, `prod`/`databricks_cluster` → `producao.staging|trusted|marts`)
- `ml_ops/` — governance rules (`validation_layer/rules.yaml`); NL2SQL agent not yet implemented

### Environment Variables

Root `.env` (copy `.env.example`):

```bash
KAGGLE_USERNAME / KAGGLE_KEY      # Kaggle dataset download
GROQ_API_KEY                      # reserved for the planned NL2SQL agent (unused)
```

Do **not** put `DATABRICKS_HOST` / `DATABRICKS_TOKEN` in the root `.env`: scripts call `load_dotenv()` and env vars take precedence over the CLI profile. Databricks auth is OAuth via `databricks auth login` (CLI profile).

`transform/.env` (copy `transform/.env.example`): `DBT_DATABRICKS_HOST`, `DBT_DATABRICKS_HTTP_PATH`, `DBT_DATABRICKS_CATALOG`, `DBT_DATABRICKS_SCHEMA`, `TARGET_ENV`. The `dev` target uses OAuth; `DBT_DATABRICKS_TOKEN` is only for `prod`.

## Tech Stack

- **Python 3.11**, PySpark, Delta Lake
- **dbt Core** + `dbt-databricks` adapter
- **Ruff** (linting), **pytest** + **pytest-mock** (tests)
- **Databricks** Lakeflow Jobs (orchestration), Unity Catalog (grants, column masks, tags)
- Planned: **LangChain** + `langchain-groq` (Llama 3), **Streamlit** UI, Docker for local dev

## Development Phases

The project is being built incrementally:
1. Infrastructure setup and documentation *(done)*
2. Data ingestion pipeline (Kaggle -> UC Volume -> Bronze Delta) *(done, validated on Databricks Free Edition)*
   - Phase 3: fictional CRM generator (`pipelines/generate_crm.py`, `make crm`) linked to Olist by `customer_unique_id`, landed in `raw.source_crm` *(done)*
3. Unit tests (pytest) *(done — `tests/pipelines/`)*
4. dbt Silver/Gold models + data tests (`docs/phase-04-dbt.md`) *(done — PASS=132)*
   - Orchestration: Lakeflow Job `Pipeline_Olist_Bronze_dbt` *(validated, run manually)*
   - UC governance (groups, grants, column masks, PII tags) *(applied via UI; governance-as-code is next)*
5. Streamlit analytics UI + NL2SQL agent *(planned)*
