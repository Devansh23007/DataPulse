
SELECT
    NULLIF(TRIM(order_id), '') AS order_id,

    NULLIF(TRIM(order_item_id), '')::INTEGER
        AS order_item_id,

    NULLIF(TRIM(product_id), '') AS product_id,
    NULLIF(TRIM(seller_id), '') AS seller_id,

    NULLIF(TRIM(shipping_limit_date), '')::TIMESTAMP
        AS shipping_limit_date,

    NULLIF(TRIM(price), '')::NUMERIC(12, 2)
        AS price,

    NULLIF(TRIM(freight_value), '')::NUMERIC(12, 2)
        AS freight_value

FROM {{ source('olist_raw', 'olist_order_items_dataset') }}
