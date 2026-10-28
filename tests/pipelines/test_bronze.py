"""
Unit tests for pipelines/bronze.py

Usa uma SparkSession local (sem Delta/Unity Catalog) para validar a leitura dos
CSVs, a normalização de colunas e os metadados. Pulado se pyspark/Java não estiverem
disponíveis.
"""

from unittest.mock import MagicMock

import pytest

pyspark = pytest.importorskip("pyspark")

from pipelines import bronze  # noqa: E402


@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession

    try:
        session = (
            SparkSession.builder.master("local[1]")
            .appName("test_bronze")
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
    except Exception as e:  # Java ausente, por exemplo
        pytest.skip(f"Spark indisponível: {e}")
    yield session
    session.stop()


def test_read_csv_handles_bom_and_multiline(spark, tmp_path):
    csv = tmp_path / "olist_order_reviews_dataset.csv"
    csv.write_text(
        '\ufeff"review_id","review comment"\n"r1","linha 1\nlinha 2"\n"r2",""\n', encoding="utf-8"
    )

    df = bronze.sanitize_column_names(bronze.read_csv(spark, str(csv)))

    assert df.columns == ["review_id", "review_comment"]
    rows = df.orderBy("review_id").collect()
    assert len(rows) == 2
    assert rows[0]["review_comment"] == "linha 1\nlinha 2"


def test_all_columns_are_strings(spark, tmp_path):
    csv = tmp_path / "olist_order_items_dataset.csv"
    csv.write_text("order_id,price\na,58.90\n")

    df = bronze.read_csv(spark, str(csv))

    assert {t for _, t in df.dtypes} == {"string"}


def test_add_metadata_columns(spark):
    df = spark.createDataFrame([("1",)], ["id"])

    out = bronze.add_metadata_columns(df, "crm", "crm_contacts.csv").collect()[0]

    assert out["_source_schema"] == "crm"
    assert out["_source_table"] == "crm_contacts.csv"
    assert out["_source_database"] == "crm_generator"
    assert out["_storage_type"] == "MANAGED"
    assert out["_ingestion_timestamp"] is not None


def test_pipeline_raises_when_a_table_fails():
    fake_spark = MagicMock()
    fake_spark.read.options.side_effect = Exception("boom")

    with pytest.raises(RuntimeError, match="1 tabela"):
        bronze.run_bronze_pipeline(fake_spark, "olist", ["/x/olist_orders_dataset.csv"])


def test_incremental_skips_existing_table():
    fake_spark = MagicMock()  # DESCRIBE TABLE não lança erro -> tabela existe

    result = bronze.ingest_file_bronze(
        fake_spark, "olist", "/x/olist_orders_dataset.csv", mode="incremental"
    )

    assert result["status"] == "SKIPPED"
    assert result["target"] == "raw.source_olist.orders"
