
SELECT
    NULLIF(TRIM(customer_id), '') AS customer_id,
    NULLIF(TRIM(customer_unique_id), '') AS customer_unique_id,

    NULLIF(
        TRIM(customer_zip_code_prefix), ''
    ) AS customer_zip_code_prefix,

    LOWER(NULLIF(TRIM(customer_city), '')) AS customer_city,
    UPPER(NULLIF(TRIM(customer_state), '')) AS customer_state

FROM {{ source('olist_raw', 'olist_customers_dataset') }}
