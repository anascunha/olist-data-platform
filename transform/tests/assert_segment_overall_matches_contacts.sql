-- A linha overall da visão por segmento deve bater com o total de contatos e receita
-- da tabela no grão de contato.
with
    overall as (
        select contacts, buyers, total_revenue
        from {{ ref('agg_crm_purchases_by_segment') }}
        where dimension_name = 'overall'
    )

    , detail as (
        select
            count(*) as contacts
            , count_if(is_marketplace_buyer) as buyers
            , sum(total_revenue) as total_revenue
        from {{ ref('agg_crm_contact_purchases') }}
    )

select *
from overall
cross join detail
where overall.contacts != detail.contacts
    or overall.buyers != detail.buyers
    or overall.total_revenue != detail.total_revenue
