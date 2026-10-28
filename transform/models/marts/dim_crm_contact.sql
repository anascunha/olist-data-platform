with
    contacts as (
        select *
        from {{ ref('tru_crm_contacts') }}
    )

    , add_surrogate_key as (
        select
            {{ dbt_utils.generate_surrogate_key(['contact_id']) }} as contact_sk
            , contact_id
            , customer_unique_id
            , is_linked_to_marketplace
            , first_name
            , last_name
            , full_name
            , email
            , phone_e164
            , birth_date
            , contact_city
            , contact_state
            , lifecycle_stage
            , lead_source
            , campaign_id
            , campaign_name
            , campaign_channel
            , owner_id
            , owner_name
            , owner_team
            , owner_region
            , owner_is_active
            , marketing_opt_in
            , created_at
            , updated_at
            , activities_count
            , first_activity_at
            , last_activity_at
        from contacts
    )

select *
from add_surrogate_key
