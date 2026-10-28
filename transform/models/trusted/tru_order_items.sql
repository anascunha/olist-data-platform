with
    order_items as (
        select
            order_id
            , order_item_id
            , product_id
            , seller_id
            , item_price
            , freight_value
        from {{ ref('stg_olist__order_items') }}
    )

    , products as (
        select
            product_id
            , product_category_name
        from {{ ref('stg_olist__products') }}
    )

    , category_translation as (
        select
            product_category_name
            , product_category_name_english
        from {{ ref('stg_olist__product_category_name_translation') }}
    )

    , joined as (
        select
            order_items.order_id
            , order_items.order_item_id
            , order_items.product_id
            , order_items.seller_id
            , coalesce(products.product_category_name, 'not registered') as product_category_name
            , coalesce(
                category_translation.product_category_name_english
                , products.product_category_name
                , 'not registered'
            ) as product_category_name_english
            , order_items.item_price
            , order_items.freight_value
        from order_items
        left join products
            on order_items.product_id = products.product_id
        left join category_translation
            on products.product_category_name = category_translation.product_category_name
    )

select *
from joined
