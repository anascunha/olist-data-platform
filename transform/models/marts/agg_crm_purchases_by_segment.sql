/*
    Visão consolidada da agg_crm_contact_purchases por dimensão do CRM, em formato longo
    (dimension_name / dimension_value) para alimentar dashboards e o agente NL2SQL.
    Grão: dimensão x valor.
*/
{%- set dimensions = ['overall', 'lead_source', 'lifecycle_stage', 'owner_team', 'buyer_segment', 'contact_state'] %}

with
    contacts as (
        select *
        from {{ ref('agg_crm_contact_purchases') }}
    )

    {% for dimension in dimensions %}
    , by_{{ dimension }} as (
        select
            '{{ dimension }}' as dimension_name
            , {{ "'all'" if dimension == 'overall' else dimension }} as dimension_value
            , count(*) as contacts
            , count_if(is_marketplace_buyer) as buyers
            , count_if(buyer_segment = 'repeat_buyer') as repeat_buyers
            , sum(total_orders) as total_orders
            , sum(total_revenue) as total_revenue
            , count_if(is_stage_outdated) as contacts_with_outdated_stage
        from contacts
        {% if dimension != 'overall' %}group by {{ dimension }}{% endif %}
    )
    {% endfor %}

    , unioned as (
        {% for dimension in dimensions %}
        select * from by_{{ dimension }}
        {% if not loop.last %}union all{% endif %}
        {% endfor %}
    )

    , metrics as (
        select
            dimension_name
            , dimension_value
            , contacts
            , buyers
            , repeat_buyers
            , total_orders
            , cast(total_revenue as decimal(14, 2)) as total_revenue
            , round(buyers / contacts, 4) as buyer_rate
            , round(repeat_buyers / nullif(buyers, 0), 4) as repeat_buyer_rate
            , cast(total_revenue / contacts as decimal(14, 2)) as revenue_per_contact
            , cast(total_revenue / nullif(total_orders, 0) as decimal(14, 2)) as avg_ticket
            , round(total_orders / nullif(buyers, 0), 2) as orders_per_buyer
            , contacts_with_outdated_stage
        from unioned
    )

select *
from metrics
