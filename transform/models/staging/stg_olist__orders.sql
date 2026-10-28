with
    source as (
        select *
        from {{ source('olist', 'orders') }}
    )

    , renamed as (
        select
            trim(cast(order_id as string)) as order_id
            , trim(cast(customer_id as string)) as customer_id
            , lower(trim(cast(order_status as string))) as order_status
            , cast(nullif(trim(order_purchase_timestamp), '') as timestamp) as purchased_at
            , cast(nullif(trim(order_approved_at), '') as timestamp) as approved_at
            , cast(nullif(trim(order_delivered_carrier_date), '') as timestamp) as delivered_to_carrier_at
            , cast(nullif(trim(order_delivered_customer_date), '') as timestamp) as delivered_to_customer_at
            , cast(nullif(trim(order_estimated_delivery_date), '') as timestamp) as estimated_delivery_at
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
