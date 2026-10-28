with
    source as (
        select *
        from {{ source('olist', 'products') }}
    )

    -- Corrige os nomes com erro de digitação da origem (product_name_lenght)
    , renamed as (
        select
            trim(cast(product_id as string)) as product_id
            , nullif(lower(trim(cast(product_category_name as string))), '') as product_category_name
            , cast(product_name_lenght as int) as product_name_length
            , cast(product_description_lenght as int) as product_description_length
            , cast(product_photos_qty as int) as product_photos_qty
            , cast(product_weight_g as int) as product_weight_g
            , cast(product_length_cm as int) as product_length_cm
            , cast(product_height_cm as int) as product_height_cm
            , cast(product_width_cm as int) as product_width_cm
            , {{ databricks_ingestion_columns() }}
        from source
    )

select *
from renamed
