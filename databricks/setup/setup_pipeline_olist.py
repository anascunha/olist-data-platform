# Databricks notebook source
# MAGIC %md
# MAGIC # Setup do Job — Pipeline Olist (Bronze → dbt)
# MAGIC
# MAGIC Cria (ou atualiza, se já existir) o Job com duas tasks:
# MAGIC
# MAGIC 1. **Ingest_Bronze** → `databricks/ingestao_bronze.py` (`source = all`): Volumes de landing → `raw.source_olist.*` e `raw.source_crm.*`
# MAGIC 2. **dbt_Build** → `dbt deps` + `dbt build` em `transform/`: Silver (`producao.staging`, `producao.trusted`) e Gold (`producao.marts`)
# MAGIC
# MAGIC A task dbt gera o profile automaticamente com target `databricks_cluster`, que a macro
# MAGIC `generate_schema_name` trata como produção.
# MAGIC
# MAGIC ⚠️ Os CSVs precisam estar nos Volumes antes da execução (`make ingest` e `make crm`).

# COMMAND ----------

# ==========================================
# WIDGETS - Configuração do Job
# ==========================================
dbutils.widgets.text("pipeline_name", "Pipeline_Olist_Bronze_dbt", "Nome do Pipeline")  # noqa: F821
dbutils.widgets.text("schedule_cron", "", "Cron Schedule (vazio = sem agendamento)")  # noqa: F821
dbutils.widgets.text("repo_path", "/Workspace/Users/<seu_usuario>/olist-data-platform", "Git folder do repositório")  # noqa: F821, E501
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID (task dbt)")  # noqa: F821

PIPELINE_NAME = dbutils.widgets.get("pipeline_name").strip()  # noqa: F821
SCHEDULE_CRON = dbutils.widgets.get("schedule_cron").strip()  # noqa: F821
REPO_PATH = dbutils.widgets.get("repo_path").rstrip("/")  # noqa: F821
WAREHOUSE_ID = dbutils.widgets.get("warehouse_id").strip()  # noqa: F821

if not WAREHOUSE_ID:
    raise ValueError("Informe o warehouse_id (SQL Warehouses → seu warehouse → Connection details).")

print(f"▶ Pipeline:  {PIPELINE_NAME}")
print(f"▶ Schedule:  {SCHEDULE_CRON or 'Sem agendamento (manual)'}")
print(f"▶ Repo:      {REPO_PATH}")
print(f"▶ Warehouse: {WAREHOUSE_ID}")

# COMMAND ----------

import requests  # noqa: E402

# Lê host e token do ambiente Databricks automaticamente
context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()  # noqa: F821
DATABRICKS_HOST = context.apiUrl().get()
HEADERS = {
    "Authorization": f"Bearer {context.apiToken().get()}",
    "Content-Type": "application/json",
}

# COMMAND ----------


def build_job_payload(pipeline_name, repo_path, warehouse_id, schedule_cron):
    payload = {
        "name": pipeline_name,
        "tasks": [
            {
                "task_key": "Ingest_Bronze",
                "notebook_task": {
                    "notebook_path": f"{repo_path}/databricks/ingestao_bronze",
                    "base_parameters": {"source": "all", "mode": "full"},
                },
            },
            {
                "task_key": "dbt_Build",
                "depends_on": [{"task_key": "Ingest_Bronze"}],
                "run_if": "ALL_SUCCESS",
                "environment_key": "dbt_env",
                "dbt_task": {
                    "project_directory": f"{repo_path}/transform",
                    "commands": ["dbt deps", "dbt build"],
                    "warehouse_id": warehouse_id,
                    "catalog": "producao",
                    "schema": "marts",
                    "source": "WORKSPACE",
                },
            },
        ],
        "environments": [
            {
                "environment_key": "dbt_env",
                "spec": {"client": "1", "dependencies": ["dbt-databricks>=1.10,<2.0"]},
            }
        ],
        "max_concurrent_runs": 1,
        "timeout_seconds": 0,
    }

    if schedule_cron:
        payload["schedule"] = {
            "quartz_cron_expression": schedule_cron,
            "timezone_id": "America/Sao_Paulo",
            "pause_status": "UNPAUSED",
        }
    return payload


def get_existing_job_id(pipeline_name):
    res = requests.get(
        f"{DATABRICKS_HOST}/api/2.1/jobs/list", headers=HEADERS, params={"name": pipeline_name}
    )
    res.raise_for_status()
    jobs = res.json().get("jobs", [])
    return jobs[0]["job_id"] if jobs else None


def create_or_update_job():
    payload = build_job_payload(PIPELINE_NAME, REPO_PATH, WAREHOUSE_ID, SCHEDULE_CRON)
    existing_id = get_existing_job_id(PIPELINE_NAME)

    if existing_id:
        res = requests.post(
            f"{DATABRICKS_HOST}/api/2.1/jobs/reset",
            headers=HEADERS,
            json={"job_id": existing_id, "new_settings": payload},
        )
        res.raise_for_status()
        job_id = existing_id
        print("Job atualizado com sucesso!")
    else:
        res = requests.post(f"{DATABRICKS_HOST}/api/2.1/jobs/create", headers=HEADERS, json=payload)
        if not res.ok:
            print(f"Erro ao criar Job: {res.status_code} {res.text}")
            res.raise_for_status()
        job_id = res.json()["job_id"]
        print("Job criado com sucesso!")

    print(f"  Job ID: {job_id}")
    print(f"  URL:    {DATABRICKS_HOST}/#job/{job_id}")
    return job_id


job_id = create_or_update_job()
