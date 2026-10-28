"""
Camada Bronze — converte os CSVs do Volume de landing em tabelas Delta gerenciadas
no Unity Catalog (raw.source_<fonte>.<tabela>).

Mesmo padrão da ingestão JDBC do Adventure Works:
  * dados preservados como vieram da fonte (todas as colunas como string);
  * nomes de colunas normalizados para Delta Lake;
  * colunas de rastreabilidade (_ingestion_timestamp, _source_*, _storage_type).
"""

from datetime import datetime

from pipelines.config import SOURCES, target_table, volume_path
from pipelines.utils import sanitize_column_name, table_name_from_file

CSV_OPTIONS = {
    "header": "true",
    "inferSchema": "false",  # tipagem acontece no staging (dbt)
    "multiLine": "true",     # order_reviews tem comentários com quebra de linha
    "escape": '"',
    "encoding": "UTF-8",
}


def sanitize_column_names(df):
    """Normaliza nomes de colunas para compatibilidade com Delta Lake."""
    for col_name in df.columns:
        df = df.withColumnRenamed(col_name, sanitize_column_name(col_name))
    return df


def add_metadata_columns(df, source, source_table):
    """Adiciona colunas de rastreabilidade e auditoria."""
    from pyspark.sql.functions import current_timestamp, lit

    return (
        df
        .withColumn("_ingestion_timestamp", current_timestamp())
        .withColumn("_source_schema",       lit(source))
        .withColumn("_source_table",        lit(source_table))
        .withColumn("_source_database",     lit(SOURCES[source]["source_database"]))
        .withColumn("_storage_type",        lit("MANAGED"))
    )


def read_csv(spark, path):
    return spark.read.options(**CSV_OPTIONS).csv(path)


def table_exists(spark, table_full_name):
    """Retorna True se a tabela já existe no Unity Catalog."""
    try:
        spark.sql(f"DESCRIBE TABLE {table_full_name}")
        return True
    except Exception:
        return False


def ingest_file_bronze(spark, source, file_path, mode="full"):
    """Ingere um CSV do Volume como MANAGED TABLE na camada Bronze."""
    file_name = file_path.rsplit("/", 1)[-1]
    table = table_name_from_file(file_name)
    target_name = target_table(source, table)

    if mode == "incremental" and table_exists(spark, target_name):
        print(f"SKIP {file_name} -> {target_name} ja existe (incremental)")
        return {"table": table, "status": "SKIPPED", "target": target_name}

    try:
        df = read_csv(spark, file_path)
        df = sanitize_column_names(df)
        df = add_metadata_columns(df, source, file_name)

        (
            df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target_name)
        )

        record_count = spark.table(target_name).count()
        table_comment = (
            f"Fonte: {SOURCES[source]['source_database']}/{file_name} | "
            f"Colunas: {len(df.columns)} | "
            f"Registros: {record_count} | "
            f"Modo: {mode.upper()} | "
            f"Storage: MANAGED | "
            f"Ingestion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        spark.sql(f"COMMENT ON TABLE {target_name} IS '{table_comment}'")

        print(f"OK {file_name} -> {target_name} [{record_count:,} registros] [SUCESSO]")
        return {"table": table, "status": "SUCCESS", "records": record_count,
                "target": target_name}

    except Exception as e:
        print(f"ERRO em {file_name}: {e}")
        return {"table": table, "status": "FAILED", "error": str(e), "target": target_name}


def run_bronze_pipeline(spark, source, file_paths, mode="full"):
    """Processa todos os CSVs de uma fonte e imprime o resumo da execução."""
    start_time = datetime.now()
    print(f"\nIniciando Bronze: fonte={source} | {len(file_paths)} arquivos | modo={mode.upper()}")
    print("=" * 80)

    results = [ingest_file_bronze(spark, source, path, mode) for path in sorted(file_paths)]

    duration = (datetime.now() - start_time).total_seconds()
    success = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]

    print("\n" + "=" * 80)
    print("RESUMO DA INGESTAO BRONZE")
    print("=" * 80)
    print(f"Fonte:            {source} ({volume_path(source)})")
    print(f"Sucesso:          {len(success)}/{len(results)}")
    print(f"Falhas:           {len(failed)}/{len(results)}")
    print(f"Total registros:  {sum(r['records'] for r in success):,}")
    print(f"Duração:          {duration:.1f}s")
    for r in failed:
        print(f"  ✗ {r['table']}: {r['error']}")

    if failed:
        raise RuntimeError(f"{len(failed)} tabela(s) falharam na ingestão Bronze")
    return results
