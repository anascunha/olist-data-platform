with
    source as (
        select *
        from {{ source('olist', 'customers') }}
    )

    , renamed as (
        select
            trim(cast(customer_id as string)) as customer_id
            , trim(cast(customer_unique_id as string)) as customer_unique_id
            , lpad(trim(cast(customer_zip_code_prefix as string)), 5, '0') as customer_zip_code_prefix
            , lower(trim(cast(customer_city as string))) as customer_city
            , upper(trim(cast(customer_state as string))) as customer_state
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
