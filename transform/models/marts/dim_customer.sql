with
    orders as (
        select
            customer_unique_id
            , customer_city
            , customer_state
            , purchased_at
        from {{ ref('tru_orders') }}
    )

    , crm_contacts as (
        select
            customer_unique_id
            , contact_id
        from {{ ref('tru_crm_contacts') }}
        where customer_unique_id is not null
    )

    -- Cidade/UF do pedido mais recente (o cliente pode ter comprado de endereços diferentes)
    , latest_address as (
        select
            customer_unique_id
            , customer_city
            , customer_state
            , row_number() over (
                partition by customer_unique_id
                order by purchased_at desc
            ) as address_recency
        from orders
    )

    , customers as (
        select
            orders.customer_unique_id
            , min(orders.purchased_at) as first_purchase_at
            , max(orders.purchased_at) as last_purchase_at
        from orders
        group by orders.customer_unique_id
    )

    , joined as (
        select
            {{ dbt_utils.generate_surrogate_key(['customers.customer_unique_id']) }} as customer_sk
            , customers.customer_unique_id
            , latest_address.customer_city
            , latest_address.customer_state
            , customers.first_purchase_at
            , customers.last_purchase_at
            , crm_contacts.contact_id is not null as is_in_crm
            , crm_contacts.contact_id
        from customers
        inner join latest_address
            on customers.customer_unique_id = latest_address.customer_unique_id
            and latest_address.address_recency = 1
        left join crm_contacts
            on customers.customer_unique_id = crm_contacts.customer_unique_id
    )

select *
from joined
