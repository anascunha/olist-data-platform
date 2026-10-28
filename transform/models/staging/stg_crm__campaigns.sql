with
    source as (
        select *
        from {{ source('crm', 'campaigns') }}
    )

    , renamed as (
        select
            trim(cast(campaign_id as string)) as campaign_id
            , trim(cast(campaign_name as string)) as campaign_name
            , lower(trim(cast(channel as string))) as campaign_channel
            , cast(start_date as date) as campaign_start_date
            , cast(end_date as date) as campaign_end_date
            , cast(budget_brl as decimal(12, 2)) as campaign_budget_brl
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
