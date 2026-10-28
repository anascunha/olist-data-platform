-- E-mails normalizados do CRM devem ter formato válido (vazios viram nulo no staging).
select
    contact_id
    , email
from {{ ref('dim_crm_contact') }}
where email is not null
    and not email rlike '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$'
