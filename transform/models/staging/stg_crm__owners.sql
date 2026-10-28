with
    source as (
        select *
        from {{ source('crm', 'owners') }}
    )

    , renamed as (
        select
            trim(cast(owner_id as string)) as owner_id
            , trim(cast(owner_name as string)) as owner_name
            , lower(trim(cast(owner_email as string))) as owner_email
            , trim(cast(team as string)) as owner_team
            , trim(cast(region as string)) as owner_region
            , cast(hired_at as date) as hired_at
            , cast(is_active as boolean) as is_active
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
