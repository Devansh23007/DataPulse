
SELECT
    oi.order_id,
    oi.order_item_id,

    o.customer_id,
    oi.product_id,
    oi.seller_id,

    o.order_status,
    o.order_purchase_timestamp,
    CAST(o.order_purchase_timestamp AS DATE) AS order_date,

    oi.shipping_limit_date,
    oi.price,
    oi.freight_value,

    oi.price + COALESCE(oi.freight_value, 0)
        AS item_total_amount

FROM {{ ref('stg_order_items') }} AS oi

INNER JOIN {{ ref('stg_orders') }} AS o
    ON oi.order_id = o.order_id
