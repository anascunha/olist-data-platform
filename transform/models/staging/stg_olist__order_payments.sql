with
    source as (
        select *
        from {{ source('olist', 'order_payments') }}
    )

    , renamed as (
        select
            trim(cast(order_id as string)) as order_id
            , cast(payment_sequential as int) as payment_sequential
            , lower(trim(cast(payment_type as string))) as payment_type
            , cast(payment_installments as int) as payment_installments
            , cast(payment_value as decimal(12, 2)) as payment_value
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
