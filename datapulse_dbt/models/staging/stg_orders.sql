
SELECT
    NULLIF(TRIM(order_id), '') AS order_id,
    NULLIF(TRIM(customer_id), '') AS customer_id,
    LOWER(NULLIF(TRIM(order_status), '')) AS order_status,

    NULLIF(
        TRIM(order_purchase_timestamp), ''
    )::TIMESTAMP AS order_purchase_timestamp,

    NULLIF(
        TRIM(order_approved_at), ''
    )::TIMESTAMP AS order_approved_at,

    NULLIF(
        TRIM(order_delivered_carrier_date), ''
    )::TIMESTAMP AS order_delivered_carrier_date,

    NULLIF(
        TRIM(order_delivered_customer_date), ''
    )::TIMESTAMP AS order_delivered_customer_date,

    NULLIF(
        TRIM(order_estimated_delivery_date), ''
    )::TIMESTAMP AS order_estimated_delivery_date

FROM {{ source('olist_raw', 'olist_orders_dataset') }}
