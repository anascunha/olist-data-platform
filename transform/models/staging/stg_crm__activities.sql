with
    source as (
        select *
        from {{ source('crm', 'activities') }}
    )

    , renamed as (
        select
            trim(cast(activity_id as string)) as activity_id
            , trim(cast(contact_id as string)) as contact_id
            , trim(cast(owner_id as string)) as owner_id
            , lower(trim(cast(activity_type as string))) as activity_type
            , lower(trim(cast(direction as string))) as activity_direction
            , cast(activity_at as timestamp) as activity_at
            , lower(trim(cast(outcome as string))) as activity_outcome
            , cast(nullif(trim(duration_minutes), '') as int) as duration_minutes
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
