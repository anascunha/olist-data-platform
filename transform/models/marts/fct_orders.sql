with
    orders as (
        select *
        from {{ ref('tru_orders') }}
    )

    , customers as (
        select
            customer_sk
            , customer_unique_id
        from {{ ref('dim_customer') }}
    )

    , contacts as (
        select
            contact_sk
            , contact_id
            , customer_unique_id
            , created_at as contact_created_at
        from {{ ref('dim_crm_contact') }}
        where customer_unique_id is not null
    )

    , joined as (
        select
            {{ dbt_utils.generate_surrogate_key(['orders.order_id']) }} as order_sk
            , orders.order_id
            , customers.customer_sk
            , contacts.contact_sk
            , orders.customer_unique_id
            , contacts.contact_id
            , orders.order_status
            , orders.is_valid_order
            , orders.purchased_at
            , orders.purchase_date
            , orders.delivered_to_customer_at
            , orders.is_delivered
            , orders.is_delivered_late
            , orders.items_quantity
            , orders.distinct_products
            , orders.products_value
            , orders.freight_value
            , orders.order_value
            , orders.payment_value
            , orders.main_payment_type
            , orders.max_payment_installments
            , contacts.contact_id is not null as is_crm_contact
            , case
                when contacts.contact_id is null then null
                else orders.purchased_at >= contacts.contact_created_at
            end as is_after_crm_entry
        from orders
        inner join customers
            on orders.customer_unique_id = customers.customer_unique_id
        left join contacts
            on orders.customer_unique_id = contacts.customer_unique_id
    )

select *
from joined
