with
    -- O export do CRM traz o mesmo contato mais de uma vez; mantém a versão mais recente
    contacts_ranked as (
        select
            *
            , row_number() over (
                partition by contact_id
                order by updated_at desc, _ingestion_timestamp desc
            ) as version_recency
        from {{ ref('stg_crm__contacts') }}
    )

    , contacts as (
        select *
        from contacts_ranked
        where version_recency = 1
    )

    , owners as (
        select
            owner_id
            , owner_name
            , owner_team
            , owner_region
            , is_active as owner_is_active
        from {{ ref('stg_crm__owners') }}
    )

    , campaigns as (
        select
            campaign_id
            , campaign_name
            , campaign_channel
            , campaign_start_date
        from {{ ref('stg_crm__campaigns') }}
    )

    , activities as (
        select
            contact_id
            , count(*) as activities_count
            , min(activity_at) as first_activity_at
            , max(activity_at) as last_activity_at
        from {{ ref('stg_crm__activities') }}
        group by contact_id
    )

    , joined as (
        select
            contacts.contact_id
            , contacts.customer_unique_id
            , contacts.customer_unique_id is not null as is_linked_to_marketplace
            , contacts.first_name
            , contacts.last_name
            , concat_ws(' ', contacts.first_name, contacts.last_name) as full_name
            , contacts.email
            , contacts.phone_e164
            , contacts.birth_date
            , contacts.contact_city
            , contacts.contact_state
            , contacts.lifecycle_stage
            , contacts.lead_source
            , contacts.campaign_id
            , coalesce(campaigns.campaign_name, 'no campaign') as campaign_name
            , campaigns.campaign_channel
            , contacts.owner_id
            , coalesce(owners.owner_name, 'not registered') as owner_name
            , coalesce(owners.owner_team, 'not registered') as owner_team
            , coalesce(owners.owner_region, 'not registered') as owner_region
            , owners.owner_is_active
            , contacts.marketing_opt_in
            , contacts.created_at
            , contacts.updated_at
            , coalesce(activities.activities_count, 0) as activities_count
            , activities.first_activity_at
            , activities.last_activity_at
        from contacts
        left join owners
            on contacts.owner_id = owners.owner_id
        left join campaigns
            on contacts.campaign_id = campaigns.campaign_id
        left join activities
            on contacts.contact_id = activities.contact_id
    )

select *
from joined
