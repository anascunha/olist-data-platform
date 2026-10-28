-- A receita atribuída aos contatos do CRM deve ser igual à soma dos pedidos válidos
-- de clientes presentes no CRM na fato.
with
    from_contacts as (
        select sum(total_revenue) as revenue
        from {{ ref('agg_crm_contact_purchases') }}
    )

    , from_orders as (
        select sum(order_value) as revenue
        from {{ ref('fct_orders') }}
        where is_valid_order
            and is_crm_contact
    )

select *
from from_contacts
cross join from_orders
where abs(from_contacts.revenue - from_orders.revenue) > 0.01
