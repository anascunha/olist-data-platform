/*
    DESCRIÇÃO: Aplica Cast e Trim aos metadados gerados pelo Databricks.
*/

{%- macro databricks_ingestion_columns() -%}
    cast(_ingestion_timestamp as timestamp) as _ingestion_timestamp,
    trim(cast(_source_schema as string)) as _source_schema,
    trim(cast(_source_table as string)) as _source_table,
    trim(cast(_source_database as string)) as _source_database,
    trim(cast(_storage_type as string)) as _storage_type
{%- endmacro -%}