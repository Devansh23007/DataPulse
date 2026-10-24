
SELECT
    order_date,
    order_status,

    COUNT(DISTINCT order_id) AS order_count,
    COUNT(*) AS order_item_count,

    COUNT(DISTINCT customer_id) AS customer_count,

    SUM(price) AS gross_item_value,
    SUM(COALESCE(freight_value, 0)) AS freight_value,

    SUM(item_total_amount) AS item_total_revenue,
    AVG(price) AS average_item_price

FROM {{ ref('fact_order_items') }}

GROUP BY
    order_date,
    order_status
