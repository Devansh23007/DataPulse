
SELECT
    NULLIF(TRIM(seller_id), '') AS seller_id,

    NULLIF(
        TRIM(seller_zip_code_prefix), ''
    ) AS seller_zip_code_prefix,

    LOWER(NULLIF(TRIM(seller_city), '')) AS seller_city,
    UPPER(NULLIF(TRIM(seller_state), '')) AS seller_state

FROM {{ source('olist_raw', 'olist_sellers_dataset') }}

