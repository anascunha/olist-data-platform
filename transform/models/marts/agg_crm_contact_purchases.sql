/*
    Responde: quais contatos do CRM compram no marketplace, quanto e com que frequência.
    Grão: um registro por contato do CRM (inclusive os que nunca compraram).
    Apenas pedidos válidos (var invalid_order_statuses) entram nas métricas.
    Recência é calculada contra a data do último pedido do dataset (snapshot histórico).
*/
with
    contacts as (
        select *
        from {{ ref('dim_crm_contact') }}
    )

    , valid_orders as (
        select
            order_id
            , contact_id
            , purchased_at
            , order_value
            , is_after_crm_entry
        from {{ ref('fct_orders') }}
        where is_valid_order
            and contact_id is not null
    )

    , reference_date as (
        select max(purchase_date) as reference_date
        from {{ ref('fct_orders') }}
    )

    , purchases as (
        select
            contact_id
            , count(*) as total_orders
            , sum(order_value) as total_revenue
            , min(purchased_at) as first_order_at
            , max(purchased_at) as last_order_at
            , count(distinct cast(purchased_at as date)) as distinct_purchase_days
            , count_if(is_after_crm_entry) as orders_after_crm_entry
            , coalesce(sum(case when is_after_crm_entry then order_value end), 0)
                as revenue_after_crm_entry
        from valid_orders
        group by contact_id
    )

    -- Categoria com maior gasto por contato
    , category_spend as (
        select
            valid_orders.contact_id
            , items.product_category_name_english
            , sum(items.item_price) as category_revenue
        from valid_orders
        inner join {{ ref('tru_order_items') }} as items
            on valid_orders.order_id = items.order_id
        group by valid_orders.contact_id, items.product_category_name_english
    )

    , favorite_category as (
        select
            contact_id
            , max_by(product_category_name_english, category_revenue) as favorite_category
        from category_spend
        group by contact_id
    )

    , joined as (
        select
            contacts.contact_sk
            , contacts.contact_id
            , contacts.customer_unique_id
            , contacts.full_name
            , contacts.contact_state
            , contacts.lifecycle_stage
            , contacts.lead_source
            , contacts.campaign_name
            , contacts.owner_name
            , contacts.owner_team
            , contacts.created_at as contact_created_at
            , contacts.activities_count
            , coalesce(purchases.total_orders, 0) > 0 as is_marketplace_buyer
            , case
                when coalesce(purchases.total_orders, 0) = 0 then 'never_bought'
                when purchases.total_orders = 1 then 'one_time_buyer'
                else 'repeat_buyer'
            end as buyer_segment
            , coalesce(purchases.total_orders, 0) as total_orders
            , cast(coalesce(purchases.total_revenue, 0) as decimal(14, 2)) as total_revenue
            , cast(purchases.total_revenue / purchases.total_orders as decimal(14, 2)) as avg_ticket
            , purchases.first_order_at
            , purchases.last_order_at
            , datediff(purchases.last_order_at, purchases.first_order_at) as customer_lifetime_days
            , case
                when purchases.total_orders > 1
                    then round(
                        datediff(purchases.last_order_at, purchases.first_order_at)
                        / (purchases.total_orders - 1)
                        , 1
                    )
            end as avg_days_between_orders
            , datediff(reference_date.reference_date, purchases.last_order_at) as recency_days
            , datediff(purchases.first_order_at, contacts.created_at) as days_from_crm_entry_to_first_order
            , coalesce(purchases.orders_after_crm_entry, 0) as orders_after_crm_entry
            , cast(coalesce(purchases.revenue_after_crm_entry, 0) as decimal(14, 2))
                as revenue_after_crm_entry
            , favorite_category.favorite_category
            -- CRM desatualizado: compra no marketplace mas segue como lead/mql/opportunity
            , coalesce(purchases.total_orders, 0) > 0
                and contacts.lifecycle_stage in ('lead', 'mql', 'opportunity') as is_stage_outdated
        from contacts
        cross join reference_date
        left join purchases
            on contacts.contact_id = purchases.contact_id
        left join favorite_category
            on contacts.contact_id = favorite_category.contact_id
    )

select *
from joined
