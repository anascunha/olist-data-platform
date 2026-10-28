with
    source as (
        select *
        from {{ source('crm', 'contacts') }}
    )

    -- Padronização 1:1 com a origem. A deduplicação (mesmo contact_id exportado mais de
    -- uma vez) acontece na trusted, que mantém a versão com maior updated_at.
    , renamed as (
        select
            trim(cast(contact_id as string)) as contact_id
            , nullif(trim(cast(customer_unique_id as string)), '') as customer_unique_id
            , trim(cast(first_name as string)) as first_name
            , trim(cast(last_name as string)) as last_name
            , nullif(lower(trim(cast(email as string))), '') as email
            -- Telefones chegam em 3 formatos; normaliza para E.164 (+55DDDNUMERO)
            , case
                when length(regexp_replace(phone, '[^0-9]', '')) = 13
                    then concat('+', regexp_replace(phone, '[^0-9]', ''))
                when length(regexp_replace(phone, '[^0-9]', '')) in (10, 11)
                    then concat('+55', regexp_replace(phone, '[^0-9]', ''))
            end as phone_e164
            , cast(birth_date as date) as birth_date
            , lower(trim(cast(city as string))) as contact_city
            , upper(trim(cast(state as string))) as contact_state
            , lower(trim(cast(lifecycle_stage as string))) as lifecycle_stage
            , lower(trim(cast(lead_source as string))) as lead_source
            , nullif(trim(cast(campaign_id as string)), '') as campaign_id
            , trim(cast(owner_id as string)) as owner_id
            , cast(marketing_opt_in as boolean) as marketing_opt_in
            , cast(created_at as timestamp) as created_at
            , cast(updated_at as timestamp) as updated_at
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
