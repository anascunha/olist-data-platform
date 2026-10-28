with
    orders as (
        select
            order_id
            , customer_id
            , order_status
            , purchased_at
            , approved_at
            , delivered_to_customer_at
            , estimated_delivery_at
        from {{ ref('stg_olist__orders') }}
    )

    , customers as (
        select
            customer_id
            , customer_unique_id
            , customer_city
            , customer_state
        from {{ ref('stg_olist__customers') }}
    )

    -- Valor do pedido: soma dos itens (produto + frete)
    , order_items as (
        select
            order_id
            , count(*) as items_quantity
            , count(distinct product_id) as distinct_products
            , count(distinct seller_id) as distinct_sellers
            , sum(item_price) as products_value
            , sum(freight_value) as freight_value
        from {{ ref('stg_olist__order_items') }}
        group by order_id
    )

    -- Pagamentos: um pedido pode ter várias formas (ex: voucher + cartão)
    , order_payments as (
        select
            order_id
            , sum(payment_value) as payment_value
            , max(payment_installments) as max_payment_installments
            , max_by(payment_type, payment_value) as main_payment_type
        from {{ ref('stg_olist__order_payments') }}
        group by order_id
    )

    , joined as (
        select
            orders.order_id
            , orders.customer_id
            , customers.customer_unique_id
            , customers.customer_city
            , customers.customer_state
            , orders.order_status
            , orders.order_status not in (
                {%- for status in var('invalid_order_statuses') %}
                '{{ status }}'{{ ',' if not loop.last }}
                {%- endfor %}
            ) as is_valid_order
            , orders.purchased_at
            , cast(orders.purchased_at as date) as purchase_date
            , orders.approved_at
            , orders.delivered_to_customer_at
            , orders.estimated_delivery_at
            , orders.delivered_to_customer_at is not null as is_delivered
            , case
                when orders.delivered_to_customer_at is null then null
                else orders.delivered_to_customer_at > orders.estimated_delivery_at
            end as is_delivered_late
            , coalesce(order_items.items_quantity, 0) as items_quantity
            , coalesce(order_items.distinct_products, 0) as distinct_products
            , coalesce(order_items.distinct_sellers, 0) as distinct_sellers
            , coalesce(order_items.products_value, 0) as products_value
            , coalesce(order_items.freight_value, 0) as freight_value
            , coalesce(order_items.products_value, 0)
                + coalesce(order_items.freight_value, 0) as order_value
            , order_payments.payment_value
            , order_payments.main_payment_type
            , order_payments.max_payment_installments
        from orders
        inner join customers
            on orders.customer_id = customers.customer_id
        left join order_items
            on orders.order_id = order_items.order_id
        left join order_payments
            on orders.order_id = order_payments.order_id
    )

select *
from joined
