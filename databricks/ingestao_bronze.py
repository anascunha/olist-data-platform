# Databricks notebook source
# MAGIC %md
# MAGIC # Ingestão Bronze — Volume de landing → Delta (Unity Catalog)
# MAGIC
# MAGIC Lê os CSVs de `/Volumes/raw/source_<fonte>/landing/` e grava tabelas Delta gerenciadas em
# MAGIC `raw.source_<fonte>.<tabela>`, com colunas de rastreabilidade.
# MAGIC
# MAGIC | Widget | Valores | Descrição |
# MAGIC |---|---|---|
# MAGIC | `source` | `olist`, `crm`, `all` | Fonte a ser ingerida |
# MAGIC | `mode` | `full`, `incremental` | `incremental` pula tabelas que já existem |
# MAGIC
# MAGIC Pré-requisito: `databricks/setup/setup_catalogs_schemas.sql` executado e CSVs enviados
# MAGIC por `pipelines/download_data.py` / `pipelines/generate_crm.py`.

# COMMAND ----------

import os
import sys

# Em Git folders a raiz do repositório já está no sys.path; garante também ao rodar
# o arquivo como workspace file.
repo_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
if repo_root not in sys.path:
    sys.path.append(repo_root)

from pipelines.bronze import run_bronze_pipeline  # noqa: E402
from pipelines.config import RAW_CATALOG, SOURCES, volume_path  # noqa: E402

# COMMAND ----------

# ==========================================
# WIDGETS - lidos pelo Databricks Job
# Defaults valem ao rodar manualmente
# ==========================================
dbutils.widgets.dropdown("source", "all", ["all", *SOURCES.keys()], "Fonte")  # noqa: F821
dbutils.widgets.dropdown("mode", "full", ["full", "incremental"], "Modo de execução")  # noqa: F821

SOURCE = dbutils.widgets.get("source")  # noqa: F821
MODE = dbutils.widgets.get("mode")  # noqa: F821

print(f"▶ Fonte: {SOURCE}")
print(f"▶ Modo:  {MODE}")

# COMMAND ----------

sources = list(SOURCES.keys()) if SOURCE == "all" else [SOURCE]

for source in sources:
    files = [
        f.path.replace("dbfs:", "")
        for f in dbutils.fs.ls(volume_path(source))  # noqa: F821
        if f.name.lower().endswith(".csv")
    ]
    if not files:
        print(f"⚠️ Nenhum CSV em {volume_path(source)} — rode o pipeline de landing primeiro.")
        continue
    run_bronze_pipeline(spark, source, files, MODE)  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verificação

# COMMAND ----------

for source in sources:
    display(spark.sql(f"SHOW TABLES IN {RAW_CATALOG}.{SOURCES[source]['schema']}"))  # noqa: F821
