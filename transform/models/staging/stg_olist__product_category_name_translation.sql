with
    source as (
        select *
        from {{ source('olist', 'product_category_name_translation') }}
    )

    , renamed as (
        select
            lower(trim(cast(product_category_name as string))) as product_category_name
            , lower(trim(cast(product_category_name_english as string))) as product_category_name_english
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
