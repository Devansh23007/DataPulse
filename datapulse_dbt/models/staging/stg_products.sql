
SELECT
    NULLIF(TRIM(product_id), '') AS product_id,

    NULLIF(
        TRIM(product_category_name), ''
    ) AS product_category_name,

    NULLIF(TRIM(product_name_lenght), '')::INTEGER
        AS product_name_length,

    NULLIF(TRIM(product_description_lenght), '')::INTEGER
        AS product_description_length,

    NULLIF(TRIM(product_photos_qty), '')::INTEGER
        AS product_photos_qty,

    NULLIF(TRIM(product_weight_g), '')::NUMERIC
        AS product_weight_g,

    NULLIF(TRIM(product_length_cm), '')::NUMERIC
        AS product_length_cm,

    NULLIF(TRIM(product_height_cm), '')::NUMERIC
        AS product_height_cm,

    NULLIF(TRIM(product_width_cm), '')::NUMERIC
        AS product_width_cm

FROM {{ source('olist_raw', 'olist_products_dataset') }}
