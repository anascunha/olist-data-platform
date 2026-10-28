with
    source as (
        select *
        from {{ source('olist', 'order_items') }}
    )

    , renamed as (
        select
            trim(cast(order_id as string)) as order_id
            , cast(order_item_id as int) as order_item_id
            , trim(cast(product_id as string)) as product_id
            , trim(cast(seller_id as string)) as seller_id
            , cast(nullif(trim(shipping_limit_date), '') as timestamp) as shipping_limit_at
            , cast(price as decimal(12, 2)) as item_price
            , cast(freight_value as decimal(12, 2)) as freight_value
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
