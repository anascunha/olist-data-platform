# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Local Development (Docker)

```bash
make setup          # Build Docker image
make up             # Start containers in background
make down           # Stop containers
make shell          # Open interactive shell inside container
make download-data  # Download Olist dataset from Kaggle
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

Tests live in `tests/` and mirror the source tree (e.g. `pipelines/download_data.py` → `tests/pipelines/test_download_data.py`). All external calls (KaggleApi, filesystem) are mocked so no credentials or network are required.

### Linting

```bash
ruff check .        # Python linting (also runs in CI)
```

### Terraform (Infrastructure)

```bash
cd infra/
terraform fmt -check -recursive   # Format check
terraform init -backend=false     # Initialize (no backend)
terraform validate                # Syntax validation
```

### CI Pipeline

The `.github/workflows/ci.yml` runs three jobs automatically:
1. Terraform format/validate checks
2. Python linting with Ruff (`ruff check .`)
3. Python unit tests (`pytest --tb=short -v`)

## Architecture

The platform implements a **Medallion Architecture** for the [Olist Brazilian E-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) with a zero-budget approach using free tiers.

### Data Layers

| Layer  | Purpose | Tool |
|--------|---------|------|
| Bronze | Raw ingestion from Kaggle | PySpark / Azure Blob |
| Silver | Cleaned, deduplicated data | PySpark on Databricks |
| Gold   | Dimensional model (Star Schema) | dbt-databricks |

### Infrastructure (Azure via Terraform)

```
Azure Resource Group
├── Storage Account (Data Lake Gen2)
│   ├── bronze/   ← raw Parquet/Delta
│   ├── silver/   ← cleaned data
│   └── gold/     ← analytics-ready
└── Databricks Workspace (Community Edition)
```

Terraform files are in `infra/` (`main.tf`, `provider.tf`, `variables.tf`).

### AI / NL2SQL Agent (planned)

LangChain + Llama 3 (via Groq API) translates natural language questions into Databricks SQL queries, exposed through a Streamlit UI. Agent code goes in `ml_ops/`.

### Key Directories

- `pipelines/` — Data ingestion scripts (Kaggle download)
- `transform/` — dbt models (not yet populated)
- `ml_ops/` — LangChain NL2SQL agent (not yet populated)
- `infra/` — Terraform IaC for Azure

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
KAGGLE_USERNAME / KAGGLE_KEY      # Kaggle dataset download
ARM_CLIENT_ID / ARM_CLIENT_SECRET / ARM_SUBSCRIPTION_ID / ARM_TENANT_ID  # Azure
DATABRICKS_HOST / DATABRICKS_TOKEN / DATABRICKS_HTTP_PATH                # Databricks
GROQ_API_KEY                      # Llama 3 via Groq
```

## Tech Stack

- **Python 3.11**, PySpark, Delta Lake
- **dbt Core** + `dbt-databricks` adapter
- **LangChain** + `langchain-groq` (Llama 3)
- **Streamlit** (analytics UI, port 8501)
- **Terraform** (Azure IaC)
- **Ruff** (linting), **pytest** + **pytest-mock** (tests)
- **Docker** / **Docker Compose** for local dev

## Development Phases

The project is being built incrementally:
1. Infrastructure setup and documentation *(done)*
2. Data ingestion pipeline
3. Unit tests (pytest) *(done — `tests/pipelines/`)*
4. dbt tests and SQL linting (sqlfluff)
5. Streamlit analytics UI
